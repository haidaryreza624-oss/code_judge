# CodeArena Judge Engine — UML and System Diagrams

## 1. System Context Diagram

Shows how the Judge Engine communicates with the Laravel CodeArena application and the external programming language tools.

```mermaid
flowchart TB
    User["Participant"]
    Admin["Administrator"]
    Laravel["Laravel CodeArena Application"]
    Judge["FastAPI Judge Engine"]
    Compiler["Language Compilers"]
    Runtime["Language Runtimes"]

    User -->|"Submit source code"| Laravel
    Admin -->|"Manage problems and test cases"| Laravel
    Laravel -->|"HTTP / JSON Request"| Judge
    Judge -->|"HTTP / JSON Response"| Laravel
    Judge -->|"Compile source code"| Compiler
    Judge -->|"Execute programs"| Runtime
```

## 2. Use Case Diagram

Shows the main actors and their interactions with the CodeArena platform and Judge Engine.

```mermaid
flowchart LR
    Participant["Participant"]
    Admin["Administrator"]
    Laravel["CodeArena Platform"]
    Judge["Judge Engine"]

    Participant --> UC1(("Submit Solution"))
    Participant --> UC2(("View Verdict"))
    Participant --> UC3(("View Submission History"))

    Admin --> UC4(("Create Problem"))
    Admin --> UC5(("Manage Test Cases"))
    Admin --> UC6(("Manage Contests"))

    UC1 --> Laravel
    UC2 --> Laravel
    UC3 --> Laravel
    UC4 --> Laravel
    UC5 --> Laravel
    UC6 --> Laravel

    Laravel --> UC7(("Send Submission for Judging"))
    Laravel --> UC8(("Check Job Status"))

    UC7 --> Judge
    UC8 --> Judge

    Judge --> UC9(("Queue Submission"))
    Judge --> UC10(("Compile Source Code"))
    Judge --> UC11(("Execute Test Cases"))
    Judge --> UC12(("Compare Output"))
    Judge --> UC13(("Generate Verdict"))
```

## 3. Class Diagram

Represents the main classes and their relationships inside the Judge Engine.

```mermaid
classDiagram
    class FastAPIApplication {
        +create_app()
        +health_check()
    }

    class SubmissionRouter {
        +create_submission()
        +get_submission_status()
    }

    class LanguageRouter {
        +get_languages()
    }

    class SubmissionRequest {
        +language: str
        +source_code: str
        +test_cases: list
        +time_limit: float
        +memory_limit: int
    }

    class TestCase {
        +stdin: str
        +expected_output: str
    }

    class QueueManager {
        +queue: asyncio.Queue
        +jobs: dict
        +workers: int
        +submit_job()
        +get_job()
        +worker()
    }

    class JudgeService {
        +judge_submission()
        +compile_source()
        +execute_test_cases()
        +generate_verdict()
    }

    class LanguageManager {
        +get_language()
        +list_languages()
    }

    class PythonExecutor {
        +execute_python()
    }

    class CppExecutor {
        +compile_cpp()
        +run_cpp()
        +cleanup()
    }

    class JavaExecutor {
        +compile_java()
        +run_java()
        +cleanup_java()
    }

    class OutputChecker {
        +compare_output()
    }

    class MemoryMonitor {
        +monitor_memory()
    }

    class LanguageConfig {
        +name: str
        +compiler: str
        +runtime: str
        +compile_args: list
        +run_args: list
    }

    FastAPIApplication --> SubmissionRouter
    FastAPIApplication --> LanguageRouter
    SubmissionRouter --> SubmissionRequest
    SubmissionRequest --> TestCase
    SubmissionRouter --> QueueManager
    QueueManager --> JudgeService
    JudgeService --> LanguageManager
    JudgeService --> PythonExecutor
    JudgeService --> CppExecutor
    JudgeService --> JavaExecutor
    JudgeService --> OutputChecker
    JudgeService --> MemoryMonitor
    LanguageManager --> LanguageConfig
    CppExecutor --> MemoryMonitor
    PythonExecutor --> MemoryMonitor
    JavaExecutor --> MemoryMonitor
```

## 4. Submission Sequence Diagram

Shows the complete process from submitting source code in Laravel to receiving the final verdict.

```mermaid
sequenceDiagram
    autonumber

    actor User
    participant Laravel
    participant JudgeAPI as Judge Engine API
    participant Queue as In-Memory Queue
    participant Worker as Judge Worker
    participant JudgeService as Judge Service

    User->>Laravel: Submit source code
    Laravel->>Laravel: Validate submission
    Laravel->>Laravel: Save submission with Pending status

    Laravel->>JudgeAPI: POST /api/v1/submissions/
    JudgeAPI->>JudgeAPI: Validate request

    alt Queue is full
        JudgeAPI-->>Laravel: HTTP 503 - Queue Full
        Laravel->>Laravel: Mark submission as Failed
    else Queue has space
        JudgeAPI->>Queue: Add judging job
        Queue-->>JudgeAPI: Job accepted
        JudgeAPI-->>Laravel: HTTP 202 - Job ID

        Laravel->>Laravel: Save job ID
        Laravel-->>User: Submission received

        Worker->>Queue: Get next job
        Queue-->>Worker: Return job
        Worker->>JudgeService: Judge submission

        JudgeService-->>Worker: Return verdict and results
        Worker->>Worker: Update job status to Completed

        Laravel->>JudgeAPI: GET /api/v1/submissions/{job_id}
        JudgeAPI-->>Laravel: Job status and result
        Laravel->>Laravel: Update submission verdict
        Laravel-->>User: Display verdict
    end
```

## 5. Internal Execution Sequence Diagram

Shows how the Judge Service processes one submission internally.

```mermaid
sequenceDiagram
    participant Queue as Queue Worker
    participant Judge as Judge Service
    participant LM as Language Manager
    participant Compiler
    participant Executor
    participant Monitor as Memory Monitor
    participant Checker as Output Checker

    Queue->>Judge: judge_submission(request)
    Judge->>LM: get_language(language)
    LM-->>Judge: Language configuration

    alt C++ or Java
        Judge->>Compiler: Compile source code
        Compiler-->>Judge: Compilation result

        alt Compilation failed
            Judge-->>Queue: Compilation Error
        else Compilation successful
            loop Each test case (up to 20)
                Judge->>Executor: Execute program with stdin
                Executor->>Monitor: Monitor memory
                Executor-->>Judge: stdout, stderr, exit code, time, memory
                Judge->>Checker: Compare actual and expected output
                Checker-->>Judge: Comparison result
                Judge->>Judge: Determine test case verdict
            end
            Judge-->>Queue: Final verdict and statistics
        end
    else Python
        loop Each test case (up to 20)
            Judge->>Executor: Execute Python source
            Executor->>Monitor: Monitor memory
            Executor-->>Judge: Execution result
            Judge->>Checker: Compare output
            Checker-->>Judge: Comparison result
        end
        Judge-->>Queue: Final verdict and statistics
    end
```

## 6. Activity Diagram

Shows the decision-making workflow of the Judge Engine.

```mermaid
flowchart TD
    Start([Start])
    Request["Receive submission request"]
    Validate["Validate submission"]
    Valid{"Request valid?"}
    Reject["Return validation error"]
    Queue["Add job to in-memory queue"]
    Worker["Worker picks up job"]
    Language["Identify programming language"]
    Compile{"Requires compilation?"}
    CompileSource["Compile source code"]
    CompileSuccess{"Compilation successful?"}
    CE["Compilation Error"]
    Execute["Execute program"]
    Timeout{"Time limit exceeded?"}
    Memory{"Memory limit exceeded?"}
    Runtime{"Runtime error?"}
    Compare["Compare actual output with expected output"]
    Correct{"Output correct?"}
    Accepted["Mark test case Accepted"]
    More{"More test cases?"}
    WA["Wrong Answer"]
    TLE["Time Limit Exceeded"]
    MLE["Memory Limit Exceeded"]
    RE["Runtime Error"]
    Final["Generate final result"]
    Cleanup["Clean temporary files"]
    Complete([Complete])

    Start --> Request
    Request --> Validate
    Validate --> Valid
    Valid -->|No| Reject
    Reject --> Complete
    Valid -->|Yes| Queue
    Queue --> Worker
    Worker --> Language
    Language --> Compile
    Compile -->|Yes| CompileSource
    CompileSource --> CompileSuccess
    CompileSuccess -->|No| CE
    CompileSuccess -->|Yes| Execute
    Compile -->|No| Execute
    Execute --> Timeout
    Timeout -->|Yes| TLE
    Timeout -->|No| Memory
    Memory -->|Yes| MLE
    Memory -->|No| Runtime
    Runtime -->|Yes| RE
    Runtime -->|No| Compare
    Compare --> Correct
    Correct -->|No| WA
    Correct -->|Yes| Accepted
    Accepted --> More
    More -->|Yes| Execute
    More -->|No| Final

    CE --> Final
    TLE --> Final
    MLE --> Final
    RE --> Final
    WA --> Final

    Final --> Cleanup
    Cleanup --> Complete
```

## 7. Component Diagram

Shows the logical organization of the Judge Engine.

```mermaid
flowchart TB
    subgraph API["API Layer"]
        Main["FastAPI Application"]
        SubmissionAPI["Submission Router"]
        LanguageAPI["Language Router"]
        Schema["Submission Schemas"]
    end

    subgraph Services["Service Layer"]
        Queue["Queue Manager"]
        Judge["Judge Service"]
        Language["Language Manager"]
        Checker["Output Checker"]
        Monitor["Memory Monitor"]
    end

    subgraph Executors["Execution Layer"]
        Python["Python Executor"]
        CPP["C++ Executor"]
        Java["Java Executor"]
    end

    subgraph External["External System Tools"]
        PythonRuntime["Python Runtime"]
        GPP["G++ Compiler"]
        JavaCompiler["Java Compiler"]
        JavaRuntime["Java Runtime"]
    end

    Main --> SubmissionAPI
    Main --> LanguageAPI
    SubmissionAPI --> Schema
    SubmissionAPI --> Queue
    Queue --> Judge
    Judge --> Language
    Judge --> Checker
    Judge --> Monitor
    Judge --> Python
    Judge --> CPP
    Judge --> Java

    Python --> PythonRuntime
    CPP --> GPP
    Java --> JavaCompiler
    Java --> JavaRuntime
```

## 8. Deployment Diagram

Shows the current development deployment architecture.

```mermaid
flowchart TB
    User["Participant Browser"]

    subgraph Machine["Development / University Server"]
        subgraph LaravelServer["Laravel Application"]
            Laravel["Laravel Backend"]
            Database[("Laravel Database")]
        end

        subgraph JudgeServer["FastAPI Judge Engine"]
            API["FastAPI HTTP Server"]
            Queue["In-Memory Queue"]
            Worker1["Worker 1"]
            Worker2["Worker 2"]
            Jobs["In-Memory Job Storage"]
        end

        subgraph ExecutionEnvironment["Host Execution Environment"]
            Python["Python Runtime"]
            GPP["G++ Compiler"]
            Java["Java JDK 21"]
        end
    end

    User --> Laravel
    Laravel --> Database
    Laravel <-->|"HTTP / JSON"| API
    API --> Queue
    API --> Jobs
    Queue --> Worker1
    Queue --> Worker2
    Worker1 --> ExecutionEnvironment
    Worker2 --> ExecutionEnvironment
```

**Deployment notes:**

- Laravel owns the main application database.
- The Judge Engine is a separate FastAPI service.
- The queue is stored in application memory.
- Two workers process queued jobs.
- Python, C++, and Java are executed using locally installed tools.
- Redis is not currently required.
- Docker is not currently required.
- OS-level sandbox isolation is not implemented.
- Restarting the Judge Engine loses queued and in-memory job data.

## 9. Submission State Machine Diagram

Shows the possible states of a submitted job.

```mermaid
stateDiagram-v2
    [*] --> Queued

    Queued --> Running: Worker picks job

    Running --> Completed: Judging finishes
    Running --> Failed: Internal processing failure

    Completed --> [*]
    Failed --> [*]
```

**Note:** The job state and the submission verdict are different concepts.

A job can be `Completed` while its verdict is `Accepted`, `Wrong Answer`, `Runtime Error`, `Time Limit Exceeded`, `Memory Limit Exceeded`, or `Compilation Error`.

## 10. Data Flow Diagram — Level 0

Shows the Judge Engine as a single process and its external communication.

```mermaid
flowchart LR
    Laravel["Laravel CodeArena Application"]
    Judge(("Judge Engine"))
    Compiler["Compilers and Runtimes"]

    Laravel -->|"Source code, language, test cases and limits"| Judge
    Judge -->|"Job ID, status and verdict"| Laravel
    Judge -->|"Compile and execute programs"| Compiler
    Compiler -->|"Compilation and execution results"| Judge
```

## 11. Data Flow Diagram — Level 1

Breaks the Judge Engine into its main processing functions.

```mermaid
flowchart TB
    Laravel["Laravel Application"]

    P1(("1. Receive and Validate Request"))
    P2(("2. Queue Management"))
    P3(("3. Language Selection"))
    P4(("4. Compilation"))
    P5(("5. Program Execution"))
    P6(("6. Output Checking"))
    P7(("7. Verdict Generation"))

    D1[("In-Memory Job Storage")]
    D2[("In-Memory Queue")]

    Tools["Compilers and Runtimes"]

    Laravel -->|"Submission request"| P1
    P1 -->|"Valid submission"| P2
    P2 --> D1
    P2 --> D2
    D2 --> P3
    P3 --> P4
    P4 <-->|"Compile source code"| Tools
    P4 -->|"Compiled program"| P5
    P5 <-->|"Execute program"| Tools
    P5 -->|"Execution output and statistics"| P6
    P6 -->|"Comparison result"| P7
    P7 -->|"Final job result"| D1
    D1 -->|"Job status and result"| Laravel
```

## 12. API Communication Sequence Diagram

Shows the API endpoints used by Laravel to communicate with the Judge Engine.

```mermaid
sequenceDiagram
    participant Laravel as Laravel Application
    participant API as FastAPI Judge Engine
    participant Queue as Queue Manager

    Laravel->>API: GET /health
    API-->>Laravel: Health status

    Laravel->>API: GET /api/v1/languages/
    API-->>Laravel: Available languages

    Laravel->>API: POST /api/v1/submissions/
    Note over Laravel,API: JSON: language, source_code, test_cases, time_limit, memory_limit

    API->>Queue: Add submission
    Queue-->>API: Job ID
    API-->>Laravel: HTTP 202 Accepted + job_id + Queued

    loop Until job finishes
        Laravel->>API: GET /api/v1/submissions/{job_id}
        API-->>Laravel: Current job status
    end

    API-->>Laravel: Completed status + verdict + test results
```

---

# Architecture Summary

| Component | Responsibility |
|---|---|
| Laravel CodeArena | Users, problems, hidden test cases, submissions, contests and database |
| FastAPI | HTTP API and request validation |
| Queue Manager | In-memory job queue and worker coordination |
| Judge Service | Compilation coordination, test execution and verdict generation |
| Language Manager | Language configuration and availability |
| Python Executor | Python source execution |
| C++ Executor | C++ compilation and execution |
| Java Executor | Java compilation and execution |
| Output Checker | Compare actual and expected output |
| Memory Monitor | Estimate process memory usage |

## Supported Languages

| Language | Compiler | Runtime |
|---|---|---|
| Python | Not required | Python |
| C++ | G++ | Compiled executable |
| Java | Javac | Java Virtual Machine |

## Current Judge Engine Configuration

| Setting | Current value |
|---|---|
| Backend framework | FastAPI |
| Main application | Laravel |
| Queue | In-memory asyncio queue |
| Workers | 2 |
| Maximum test cases per request | 20 |
| Supported languages | Python, C++, Java |
| Queue persistence | None |
| Redis | Not used |
| Docker | Not used |
| OS-level isolation | Not implemented |
| Communication | HTTP / JSON |

## Important Implementation Limitations

1. The queue and job records are held in memory and are lost when the service restarts.
2. The current execution environment does not provide OS-level sandbox isolation.
3. Memory monitoring is approximate and does not enforce a strict operating-system memory limit.
4. Each test case starts a separate execution process. C++ and Java compilation happens once per submission, while Python source is executed for each test case.
5. The Judge Engine is designed as a separate service; Laravel remains responsible for the application's business logic and persistent database.

**End of Document**
