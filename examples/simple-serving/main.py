from metaml.serve import Serve

@Serve(package={'name': 'simple-serve', 'repository': 'wbuchwalter', 'publish': True})
def func(name):
  return "hello {}".format(name)

# if __name__ == "__main__":
func()

# from flask import Flask; app = Flask(__name__)

# def func(name):
#   return "hello {}".format(name)

# def configure():

#   def callback():
#       return func('michel')
#   # app.route('/predict')
  

# # if __name__ == "__main__":
# print('yea')
# configure()





