import numpy as np
from tasks import get_alpha1
security_id_list=[["600020", "600021"],["600022", "600023"]]
if __name__ == '__main__':
  for i in security_id_list:
    result = get_alpha1.delay(i, np.datetime64('2020-01-01'), np.datetime64('2020-01-31'))
    print(result)
