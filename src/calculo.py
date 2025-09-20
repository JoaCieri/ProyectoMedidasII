import numpy as np
import statistics
import math
from decimal import Decimal

ra = 0.45   # resistencia del amperímetro (ohm)
rv = 10e6   # resistencia del voltímetro (ohm)
fuente_instru_v= 5e-2/math.sqrt(3) #[%]
fuente_instru_i= 8e-2/math.sqrt(3) #[%]
fuente_rv= 5 #[%]
fuente_ra= 5 #[%]
cuenta_v=5
cuenta_i=20

selector=1 #0 = TBM ; 1 = CBM

# Vector de corrientes TBM [A]
i_tbm = [2.196e-3, 2.197e-3, 2.196e-3, 2.197e-3, 2.196e-3]
# Vector de tensiones TBM [V]
v_tbm = [21.985 , 21.985 , 21.985 , 21.985 , 21.985]

# Vector de corrientes CBM [A]
i_cbm = [2.191e-3, 2.189e-3, 2.190e-3, 2.188e-3, 2.191e-3]
# Vector de tensiones CBM [V]
v_cbm = [21.978, 21.978, 21.978, 21.978, 21.978]

if selector == 0 :
    
    media_i_tbm = statistics.mean(i_tbm)
    print("Media de I TBM =", media_i_tbm)
    x=Decimal(media_i_tbm)
    entero_i = int(str(x.normalize()).replace(".", "").lstrip("0")[:4])
    print("recortado=", entero_i)
    media_v_tbm = statistics.mean(v_tbm)
    print("Media de V TBM =", media_v_tbm)
    
    media_r_tbm=media_v_tbm/media_i_tbm
    print("Media de R =", media_r_tbm)
    
    errorm_tbm = (-media_r_tbm)/rv
    errorm_tbm_porcentual=errorm_tbm*100
    rcorr_tbm=media_r_tbm/(1+errorm_tbm)
    
    desvio_i_tbm = statistics.stdev(i_tbm)
    desvio_v_tbm = statistics.stdev(v_tbm)

    rep_v_tbm = (desvio_v_tbm*100)/(math.sqrt(len(i_tbm))*media_v_tbm)   
    rep_i_tbm = (desvio_i_tbm*100)/(math.sqrt(len(v_tbm))*media_i_tbm) 
    
    entero_v = int(str(media_v_tbm).replace(".", ""))
    
    print("Entero V=", entero_v)
    
    cuenta_v_tbm=(cuenta_v*100)/(math.sqrt(3)*entero_v) 
    cuenta_i_tbm=(cuenta_i*100)/(math.sqrt(3)*entero_i)
    print("Cuenta V=", cuenta_v_tbm)
    print("Cuenta I=", cuenta_i_tbm)    
    
    Coef_sens_vind_tbm=1/(1-(media_r_tbm/rv))
    Coef_sens_iind_tbm=1/((media_r_tbm/rv)-1)
    Coef_sens_rv_tbm=1/(1-(rv/media_r_tbm))
    
    f_v=pow(Coef_sens_vind_tbm*rep_v_tbm,2)
    f_ins_v=pow(Coef_sens_vind_tbm*fuente_instru_v,2)
    f_cuenta_v=pow(Coef_sens_vind_tbm*cuenta_v_tbm,2)
    f_i=pow(Coef_sens_iind_tbm*rep_i_tbm,2)
    f_ins_i=pow(Coef_sens_iind_tbm*fuente_instru_i,2)
    f_cuenta_i=pow(Coef_sens_iind_tbm*cuenta_i_tbm,2)
    f_rv=pow((fuente_rv*Coef_sens_rv_tbm)/math.sqrt(3),2)
    print("1=", f_v)
    print("2=", f_ins_v)
    print("3=", f_cuenta_v)
    print("4=", f_i)
    print("5=", f_ins_i)
    print("6=", f_cuenta_i)
    print("7=", f_rv)
    
    
    
    Uc= math.sqrt(f_v+f_ins_v+f_cuenta_v+f_i+f_ins_i+f_cuenta_i+f_rv)
    print("Uc =", Uc)
    
    Vef = pow(Uc,4)/((pow(f_v, 2)/(len(v_tbm)))+(pow(f_i, 2)/(len(i_tbm)))) 
    print("Vef= ", Vef)
    
    if Vef >= 30:
        K_tbm=2
    else: 
        K_tbm=1.85
    
    U_exp = K_tbm * Uc

    print(f"R: {rcorr_tbm} ± {U_exp}")  
    
    
if selector == 1 :
    # ====== CBM ======
    media_i_cbm = statistics.mean(i_cbm)
    print("Media de I CBM =", media_i_cbm)
    x_cbm = Decimal(media_i_cbm)
    entero_i_cbm = int(str(x_cbm.normalize()).replace(".", "").lstrip("0")[:4])
    print("recortado=", entero_i_cbm)

    media_v_cbm = statistics.mean(v_cbm)
    print("Media de V CBM =", media_v_cbm)

    media_r_cbm = media_v_cbm / media_i_cbm
    print("Media de R =", media_r_cbm)

    # Corrección por RA (voltímetro mide R+RA, amperímetro en serie)
    rcorr_cbm = media_r_cbm - ra

    # Desvíos (repetibilidad)
    desvio_i_cbm = statistics.stdev(i_cbm)
    desvio_v_cbm = statistics.stdev(v_cbm)

    rep_v_cbm = (desvio_v_cbm*100)/(math.sqrt(len(i_cbm))*media_v_cbm)
    rep_i_cbm = (desvio_i_cbm*100)/(math.sqrt(len(v_cbm))*media_i_cbm)

    entero_v_cbm = int(str(media_v_cbm).replace(".", ""))
    print("Entero V=", entero_v_cbm)

    cuenta_v_cbm = (cuenta_v*100)/(math.sqrt(3)*entero_v_cbm)
    cuenta_i_cbm = (cuenta_i*100)/(math.sqrt(3)*entero_i_cbm)
    print("Cuenta V=", cuenta_v_cbm)
    print("Cuenta I=", cuenta_i_cbm)


    Coef_sens_vind_cbm = 1/(1-(ra/media_r_cbm))
    Coef_sens_iind_cbm = 1/((ra/media_r_cbm)-1)
    Coef_sens_ra_cbm = 1/(1-(media_r_cbm/ra))

    f_v_cbm       = pow(Coef_sens_vind_cbm*rep_v_cbm,2)
    f_ins_v_cbm   = pow(Coef_sens_vind_cbm*fuente_instru_v,2)
    f_cuenta_v_cbm= pow(Coef_sens_vind_cbm*cuenta_v_cbm,2)
    f_i_cbm       = pow(Coef_sens_iind_cbm*rep_i_cbm,2)
    f_ins_i_cbm   = pow(Coef_sens_iind_cbm*fuente_instru_i,2)
    f_cuenta_i_cbm= pow(Coef_sens_iind_cbm*cuenta_i_cbm,2)
    f_ra_cbm      = pow((fuente_ra*Coef_sens_ra_cbm)/math.sqrt(3),2)

    print("1=", f_v_cbm)
    print("2=", f_ins_v_cbm)
    print("3=", f_cuenta_v_cbm)
    print("4=", f_i_cbm)
    print("5=", f_ins_i_cbm)
    print("6=", f_cuenta_i_cbm)
    print("7=", f_ra_cbm)

    Uc_cbm = math.sqrt(
        f_v_cbm + f_ins_v_cbm + f_cuenta_v_cbm +
        f_i_cbm + f_ins_i_cbm + f_cuenta_i_cbm +
        f_ra_cbm
    )
    print("Uc =", Uc_cbm)

    Vef_cbm = pow(Uc_cbm,4)/((pow(f_v_cbm,2)/len(v_cbm)) + (pow(f_i_cbm,2)/len(i_cbm)))
    print("Vef= ", Vef_cbm)

    if Vef_cbm >= 30:
        K_cbm = 2
    else:
        K_cbm = 1.85

    U_exp_cbm = K_cbm * Uc_cbm
    print(f"R: {rcorr_cbm} ± {U_exp_cbm}")