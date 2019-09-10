
MINING_REWARD = 10

MINING = 'MINING'



'''Successful responses 2xx'''

'''200 Ok 
The request has succeeded. The meaning of the success depends on the HTTP method:
'''
STATUS_200 = 200
 
'''201 Created
The request has succeeded and a new resource has been created as a result. This is typically the response sent after POST requests, or some PUT requests.
'''
STATUS_201 = 201


'''202 Accepted
The request has been received but not yet acted upon. It is noncommittal,
 since there is no way in HTTP to later send an asynchronous response indicating the outcome of the request.
  It is intended for cases where another process or server handles the request, or for batch processing.
'''
STATUS_202 = 202




'''Client error responses 4xx'''

'''
400 Bad Request
The server could not understand the request due to invalid syntax.
'''
STATUS_400 = 400


'''
401 Unauthorized
Although the HTTP standard specifies "unauthorized", semantically this response means "unauthenticated". That is, the client must authenticate itself to get the requested response.
'''
STATUS_401 = 401



'''
409 Conflict
This response is sent when a request conflicts with the current state of the server.
'''
STATUS_409 = 409

'''Server error responses 5xx'''

'''
500 Internal Server Error
The server has encountered a situation it doesn't know how to handle.
'''
STATUS_500 = 500

'''501 Not Implemented
The request method is not supported by the server and cannot be handled.
 The only methods that servers are required to support (and therefore that must not return this code) are GET and HEAD.
'''
STATUS_501 = 501













