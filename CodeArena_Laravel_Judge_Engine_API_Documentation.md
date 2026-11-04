# CodeArena Laravel ↔ Judge Engine API Documentation

This document explains how the Laravel application communicates with the
Python FastAPI Judge Engine to submit source code, send test cases,
check submission status, and retrieve final verdicts.

## 1. Architecture

The application has two separate responsibilities:

-   **Laravel --- CodeArena:** users, problems, test cases, submissions,
    contests, leaderboards, and the application database.
-   **Python --- Judge Engine:** queue submissions, compile and execute
    code, compare outputs, and return verdicts.

The important rule is:

> **Laravel owns the data. The Judge Engine only executes submissions.**

For example, Laravel stores each problem and its hidden test cases. When
a participant submits code, Laravel sends the source code and test cases
to the Judge Engine. The Judge Engine executes the code and returns the
result. Laravel then stores that result in its own database.

## 2. Judge Engine API information

Assuming the Judge Engine is running locally:

  Setting                         Value
  ------------------------------- ------------------------------------
  Base URL                        `http://127.0.0.1:8000`
  API version                     `v1`
  Request format                  JSON
  Response format                 JSON
  Submission endpoint             `POST /api/v1/submissions/`
  Status endpoint                 `GET /api/v1/submissions/{job_id}`
  Languages endpoint              `GET /api/v1/languages/`
  Interactive API documentation   `/docs`

The Judge Engine currently has no API authentication. Keep it accessible
only to trusted local services until authentication and execution
isolation are implemented.

## 3. Submitting source code

Laravel sends an HTTP POST request to:

``` http
POST http://127.0.0.1:8000/api/v1/submissions/
Content-Type: application/json
```

### Request body

``` json
{
    "language": "python",
    "source_code": "a, b = map(int, input().split())\nprint(a + b)",
    "test_cases": [
        {
            "stdin": "2 3\n",
            "expected_output": "5\n"
        },
        {
            "stdin": "10 20\n",
            "expected_output": "30\n"
        }
    ],
    "time_limit": 2,
    "memory_limit": 128000
}
```

### Request fields

  Field               Description
  ------------------- ----------------------------------------------------
  `language`          Programming language. Currently `python` or `cpp`.
  `source_code`       Source code submitted by the participant.
  `test_cases`        Test cases Laravel sends for execution.
  `stdin`             Input provided to the submitted program.
  `expected_output`   Output expected from the submitted program.
  `time_limit`        Maximum execution time per test case, in seconds.
  `memory_limit`      Memory threshold, in KB.

**Important:** The time limit applies to each test case individually.
The memory limit is currently checked after execution using approximate
memory monitoring; it is not yet an operating-system-enforced limit.

### Successful response

The API returns HTTP `202 Accepted`:

``` json
{
    "job_id": "job_76d6f565df92",
    "job_status": "Queued"
}
```

This does not mean the submitted solution has been accepted. It means
the Judge Engine has accepted the job into its queue.

Laravel must save the returned `job_id` so it can retrieve the result
later.

## 4. Checking submission status

Laravel uses the `job_id` returned by the previous request:

``` http
GET http://127.0.0.1:8000/api/v1/submissions/job_76d6f565df92
```

### Job statuses

  Job status    Meaning
  ------------- ---------------------------------------------------
  `Queued`      Waiting for an available worker.
  `Running`     Code is being compiled or executed.
  `Completed`   Execution has finished and a result is available.
  `Failed`      The Judge Engine encountered an internal failure.

When the job is still queued or running, `result` will be `null`.

### Completed response

``` json
{
    "job_id": "job_76d6f565df92",
    "job_status": "Completed",
    "result": {
        "status": "Accepted",
        "passed_test_cases": 2,
        "total_test_cases": 2,
        "execution_time": 0.195,
        "test_results": [
            {
                "test_case": 1,
                "status": "Accepted",
                "stdout": "5\n",
                "stderr": "",
                "execution_time": 0.0882,
                "memory_usage": 12000
            },
            {
                "test_case": 2,
                "status": "Accepted",
                "stdout": "30\n",
                "stderr": "",
                "execution_time": 0.1068,
                "memory_usage": 12000
            }
        ]
    }
}
```

The memory values above are illustrative. Actual values depend on the
execution environment.

### Possible verdicts

  -----------------------------------------------------------------------
  Verdict                             Meaning
  ----------------------------------- -----------------------------------
  `Accepted`                          All test cases passed.

  `Wrong Answer`                      Program output did not match
                                      expected output.

  `Time Limit Exceeded`               Program exceeded the time limit.

  `Memory Limit Exceeded`             Measured memory exceeded the
                                      configured threshold.

  `Runtime Error`                     Program exited with an error.

  `Compilation Error`                 C++ compilation failed.

  `Internal Error`                    An execution or Judge Engine error
                                      occurred.
  -----------------------------------------------------------------------

The Judge Engine stops processing further test cases after the first
unsuccessful test case. Therefore, `passed_test_cases` represents the
number passed before the first failure.

## 5. Checking supported languages

Laravel can retrieve the languages currently configured on the Judge
Engine:

``` http
GET http://127.0.0.1:8000/api/v1/languages/
```

Example response:

``` json
{
    "languages": [
        {
            "id": 1,
            "name": "C++",
            "available": true,
            "needs_compilation": true
        },
        {
            "id": 2,
            "name": "Python",
            "available": true,
            "needs_compilation": false
        }
    ]
}
```

The `available` field indicates whether the required compiler or runtime
is detected on the server. Laravel can use this endpoint to display
available languages in its submission form.

## 6. Laravel implementation

The recommended approach is to create a dedicated Laravel service class
for all communication with the Judge Engine.

Do not put HTTP requests directly inside controllers. This keeps the
application organized and makes it easier to change the Judge Engine API
later.

### Step 1 --- Configure the Judge Engine URL

Add this to the Laravel `.env` file:

``` env
JUDGE_ENGINE_URL=http://127.0.0.1:8000
```

Add the following configuration to `config/services.php`:

``` php
'judge' => [
    'url' => env('JUDGE_ENGINE_URL', 'http://127.0.0.1:8000'),
],
```

If Laravel and the Judge Engine run on separate machines, replace
`127.0.0.1` with the Judge Engine server's reachable address. If they
run in separate containers, use the appropriate service hostname
instead.

### Step 2 --- Create the JudgeService

Create this file:

``` text
app/Services/JudgeService.php
```

Paste the following code:

``` php
<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;

class JudgeService
{
    protected string $baseUrl;

    public function __construct()
    {
        $this->baseUrl = rtrim(
            config('services.judge.url'),
            '/'
        );
    }

    public function submit(array $data): array
    {
        $response = Http::timeout(15)
            ->post(
                $this->baseUrl . '/api/v1/submissions/',
                $data
            );

        $response->throw();

        return $response->json();
    }

    public function getSubmission(string $jobId): array
    {
        $response = Http::timeout(10)
            ->get(
                $this->baseUrl . '/api/v1/submissions/' . $jobId
            );

        $response->throw();

        return $response->json();
    }

    public function getLanguages(): array
    {
        $response = Http::timeout(10)
            ->get(
                $this->baseUrl . '/api/v1/languages/'
            );

        $response->throw();

        return $response->json();
    }
}
```

This service provides three methods:

-   `submit()` sends source code and test cases to the Judge Engine.
-   `getSubmission()` retrieves a job's current status and result.
-   `getLanguages()` retrieves available programming languages.

Laravel's built-in HTTP client handles JSON encoding and decoding.

### Step 3 --- Example usage in a controller

For example, create a submission controller method:

``` php
<?php

namespace App\Http\Controllers;

use App\Services\JudgeService;
use Illuminate\Http\Request;

class SubmissionController extends Controller
{
    public function store(Request $request, JudgeService $judge)
    {
        $validated = $request->validate([
            'language' => 'required|string',
            'source_code' => 'required|string',
        ]);

        $testCases = [
            [
                'stdin' => "2 3\n",
                'expected_output' => "5\n",
            ],
            [
                'stdin' => "10 20\n",
                'expected_output' => "30\n",
            ],
        ];

        $job = $judge->submit([
            'language' => $validated['language'],
            'source_code' => $validated['source_code'],
            'test_cases' => $testCases,
            'time_limit' => 2,
            'memory_limit' => 128000,
        ]);

        return response()->json($job, 202);
    }
}
```

This is a demonstration using hardcoded test cases. In the real
CodeArena application, Laravel must retrieve the problem's test cases
from its database instead.

### Step 4 --- Define the Laravel routes

In `routes/api.php`:

``` php
use App\Http\Controllers\SubmissionController;
use Illuminate\Support\Facades\Route;

Route::middleware('auth:sanctum')->group(function () {
    Route::post('/submissions', [SubmissionController::class, 'store']);
});
```

This protects the Laravel submission endpoint so only authenticated
users can submit code. The Judge Engine itself does not currently
authenticate Laravel requests.

### Step 5 --- Retrieve a submission result

Add another method to `SubmissionController`:

``` php
public function show(string $jobId, JudgeService $judge)
{
    $job = $judge->getSubmission($jobId);

    return response()->json($job);
}
```

Add its route:

``` php
Route::get('/submissions/{jobId}', [SubmissionController::class, 'show']);
```

For the actual CodeArena application, do not allow users to query
arbitrary job IDs. Retrieve the corresponding submission from your
database, verify that it belongs to the authenticated user (or that the
user is an authorized admin), and then query its stored `job_id`.

## 7. Recommended database workflow

The Laravel database should store the submission independently of the
Judge Engine's temporary job data.

A submission record could contain:

  Column                Purpose
  --------------------- --------------------------------------
  `id`                  Laravel submission ID.
  `user_id`             Participant who submitted.
  `problem_id`          Problem being solved.
  `language`            Programming language.
  `source_code`         Submitted source code.
  `judge_job_id`        Job ID returned by the Judge Engine.
  `status`              Current judging state or verdict.
  `passed_test_cases`   Number of passed test cases.
  `total_test_cases`    Number of test cases.
  `execution_time`      Total measured execution time.
  `memory_usage`        Peak measured memory, if recorded.
  `created_at`          Submission time.

Additional fields can be added for compilation errors, execution
details, and other statistics.

### Complete submission lifecycle

1.  **Participant submits code.** Laravel receives the source code,
    selected language, and problem ID.
2.  **Laravel validates the request.** It checks authentication, problem
    availability, language, and source code.
3.  **Laravel creates a submission record.** Initially, its status can
    be `Pending`.
4.  **Laravel retrieves hidden test cases.** It loads the problem's test
    cases from its own database.
5.  **Laravel sends the job to the Judge Engine.** The Judge Engine
    returns a `job_id`.
6.  **Laravel stores the job ID.** The submission status becomes
    `Queued`.
7.  **Judge Engine executes the code.** The job moves through `Queued` →
    `Running` → `Completed`.
8.  **Laravel retrieves the result.** It obtains the final verdict and
    execution statistics.
9.  **Laravel updates its submission record.** It stores the verdict,
    passed test cases, execution time, and other available information.
10. **Participant sees the result.** Laravel displays the final verdict
    on the submission page.

## 8. Important implementation considerations

1.  **Never send test cases from the browser.** The browser should send
    only the problem ID, language, and source code. Laravel retrieves
    the hidden test cases itself.
2.  **Do not wait for execution inside the submission request.** Return
    the submission ID and queued status immediately. A Laravel
    background job can retrieve the Judge Engine result.
3.  **Do not expose hidden test cases or expected outputs.** Store them
    in Laravel and only return appropriate information to the
    participant.
4.  **Handle communication failures.** If the Judge Engine is
    unavailable or its queue is full, Laravel should handle the error
    and update the submission appropriately.
5.  **Use the Laravel submission ID for your application.** Keep the
    Judge Engine's `job_id` as an external reference, not as the primary
    submission identifier.
6.  **Do not trust the current engine for public submissions yet.** It
    still executes code without isolation. Keep it restricted to trusted
    local testing until sandboxing and authentication are implemented.

## 9. Final API reference

  --------------------------------------------------------------------------------
  Method                  Endpoint                         Purpose
  ----------------------- -------------------------------- -----------------------
  `POST`                  `/api/v1/submissions/`           Submit source code.

  `GET`                   `/api/v1/submissions/{job_id}`   Retrieve job status and
                                                           result.

  `GET`                   `/api/v1/languages/`             List supported
                                                           languages.
  --------------------------------------------------------------------------------

## 10. Recommended next step

Once this integration is implemented in CodeArena, use a Laravel Queue
Job such as `ProcessSubmissionResult` to check the Judge Engine in the
background. The participant should not have to keep the browser request
open while the Judge Engine executes their code.

This document describes the integration contract based on the current
Judge Engine implementation. Any future API changes should be reflected
here.
