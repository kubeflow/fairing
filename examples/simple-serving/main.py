from metaml.serve import Serve

@Serve(package={'name': 'simple-serve', 'repository': '<your-repository-name>', 'publish': True})
def func():
  return "hello world"

if __name__ == "__main__":
  func()
