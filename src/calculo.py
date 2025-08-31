import numpy as np
import statistics

ra = 5   # resistencia del amperímetro (ohm)
rv = 5   # resistencia del voltímetro (ohm)

# Vector de corrientes (ejemplo con 5 valores)
i = [2.01, 2.05, 1.98, 2.00, 2.02]
# Vector de tensiones (ejemplo con 5 valores)
v = [10.1, 10.3, 9.9, 10.2, 10.0]

media_i = statistics.mean(i)
print("Media de I =", media_i)
media_v = statistics.mean(v)
print("Media de V =", media_v)

media_r=media_v/media_i
print("Media de V =", media_r)

errorm_tbm= (-media_r)/rv
errorm_tbm_porcentual=errorm_tbm*100

errorm_cbm=(ra)/(media_r-ra)

rcorr_tbm=media_r/(1+errorm_tbm)
rcorr_cbm=media_r/(1+errorm_cbm)
