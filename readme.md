# llll

Perform your python tasks in parallel with ease.

## Installation

```bash
git clone https://github.com/ctmakro/llll
cd llll
pip install -e .
```

## Usage

- Start a child process and collect every line from its `stdout` asynchronously via callback.

    The callbacks will be initiated from a separate thread.

    ```python
    from llll import Subprocess
    import sys,time

    def decode_and_print(bytes):
      sys.stdout.write(bytes.decode('utf-8'))
      sys.stdout.flush()

    s = Subprocess(
      ['ping','baidu.com'],
      # args

      stdout_callback = decode_and_print,
      stderr_callback = decode_and_print,
      # fire each time a new line arrives

      end_callback = None,
      # fires on process exit
      # func(string stdout, string stderr)

      collect_output = False,
      # if set to true, collect the entire stdout/stderr and pass them to end_callback

      verbose = True,
      # print auxiliary info
    )

    time.sleep(5)
    s.kill()
    s.join()
    ```

- Start a python script in a separate process and exchange python objects with it.

  Good for scenarios where the `multiprocessing` package doesn't fit. For example when you don't want to run the master's script again (may have side effect) to instantiate a slave.

  For inter-process communication, `multiprocessing` suggest using a `Queue` based on pipes, while here we implemented a replacement using `Socket`. You may `send()` anything that is pickle-able and `recv()` it from the other side.

  The new python process's `stdin` is closed on initialization.

  ```python
  from llll import PythonInstance
  import time

  code = '''
  from llll import sbc
  sbc = sbc()

  import time
  while True:
    obj = sbc.recv()
    if obj == 'stop':
        sbc.send('ok, stopped')
        break
    else:
        print(obj + '!')
    time.sleep(0.5)
  '''

  pi = PythonInstance(code)

  # for each string we send, the slave will print with an exclamation mark.
  # the slave's stdout is directed to the master's stdout so we can see it.
  pi.send('hello')
  pi.send('world')
  pi.send('yeah')

  # if the string we send is 'stop', the slave will respond and exit
  pi.send('stop')

  # receive and print the response from slave side
  print(pi.recv())

  time.sleep(1)
  pi.join()
  ```

  You have to deal with all exceptions in the started script to prevent it from exiting. We offer no inter-process error handling; you can implement that yourself, or use the Pyro library instead, which supports inter-process error handling over Internet.
