import { exec } from 'child_process';

interface ToolContext {
  readonly fs: typeof import('fs');
  readonly path: typeof import('path');
  readonly os: typeof import('os');
  readonly process: typeof import('process');
  readonly httpClient: {
    request<TInput = unknown, TOutput = unknown>(
      url: URL,
      method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD',
      options?: {
        timeout?: number;
        retryStrategy?: { maxAttempts: number; maxElapsedTime: number };
        body?: TInput;
        headers?: Record<string, string>;
        compression?: 'gzip' | 'br';
        doNotParse?: TOutput extends Buffer ? boolean : never;
      }
    ): Promise<{ statusCode: number; headers: Record<string, string | string[] | undefined>; body: TOutput }>;
  };
  readonly rootDir: string;
  readonly validFileGlobs: string[];
  readonly excludedFileGlobs: string[];
}

interface PythonTestRunnerParams {
  testPath?: string;
  virtual?: boolean;
  rotation?: number;
  mirror?: boolean;
  unitTests?: boolean;
  integrationTests?: boolean;
}

class PythonTestRunner {
  constructor(private context: ToolContext) {}

  readonly name = 'PythonTestRunner';

  readonly description = 'Executes Python unit and integration tests for the IT8951 e-ink display driver, with support for virtual display mode and display configuration options.';

  readonly inputSchema = {
    json: {
      type: 'object',
      properties: {
        testPath: {
          type: 'string',
          description: 'Specific test file or directory to run (optional)'
        },
        virtual: {
          type: 'boolean',
          description: 'Run tests in virtual display mode (default: false)'
        },
        rotation: {
          type: 'number',
          description: 'Display rotation in degrees (0, 90, 180, or 270)'
        },
        mirror: {
          type: 'boolean',
          description: 'Mirror the display output (default: false)'
        },
        unitTests: {
          type: 'boolean',
          description: 'Run unit tests (default: true)'
        },
        integrationTests: {
          type: 'boolean',
          description: 'Run integration tests (default: true)'
        }
      }
    }
  };

  async execute(params: PythonTestRunnerParams) {
    const {
      testPath,
      virtual = false,
      rotation = 0,
      mirror = false,
      unitTests = true,
      integrationTests = true
    } = params;

    if (!unitTests && !integrationTests) {
      return {
        status: 'error',
        message: 'At least one of unitTests or integrationTests must be true'
      };
    }

    if (rotation && ![0, 90, 180, 270].includes(rotation)) {
      return {
        status: 'error',
        message: 'Rotation must be one of: 0, 90, 180, 270'
      };
    }

    const commands: string[] = [];

    if (testPath) {
      // Run specific test file or directory
      const args = [];
      if (virtual) args.push('-v');
      if (rotation) args.push('-r', rotation.toString());
      if (mirror) args.push('-m');
      commands.push(`python3 ${testPath} ${args.join(' ')}`);
    } else {
      // Run selected test suites
      if (unitTests) {
        commands.push('python3 -m pytest IT8951/test/unit/');
      }
      if (integrationTests) {
        const args = [];
        if (virtual) args.push('-v');
        if (rotation) args.push('-r', rotation.toString());
        if (mirror) args.push('-m');
        commands.push(`python3 IT8951/test/integration/test.py ${args.join(' ')}`);
      }
    }

    const results: any[] = [];
    for (const command of commands) {
      try {
        const result = await new Promise<any>((resolve) => {
          exec(command, { cwd: this.context.rootDir }, (error, stdout, stderr) => {
            if (error) {
              resolve({
                status: 'error',
                command,
                message: 'Test execution failed:',
                error: error.message,
                stderr
              });
            } else {
              resolve({
                status: 'success',
                command,
                message: 'Tests executed successfully:',
                output: stdout
              });
            }
          });
        });
        results.push(result);
      } catch (error: any) {
        results.push({
          status: 'error',
          command,
          message: 'Test execution failed:',
          error: error.message
        });
      }
    }

    return {
      status: results.every(r => r.status === 'success') ? 'success' : 'error',
      results
    };
  }
}

export default PythonTestRunner;
