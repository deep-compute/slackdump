from operator import attrgetter

def memoize(f):
    # from: https://goo.gl/aXt4Qy
    class memodict(dict):
        __slots__ = ()
        def __missing__(self, key):
            self[key] = ret = f(key)
            return ret
    return memodict().__getitem__

@memoize
def load_object(imp_path):
    '''
    Given a path (python import path), load the object.
    eg of path: logagg.formatters.nginx_access
              : logagg.forwarders.mongodb
    '''
    module_name, obj_name = imp_path.split('.', 1)
    module = __import__(module_name)
    obj = attrgetter(obj_name)(module)
    return obj

