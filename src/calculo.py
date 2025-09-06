import numpy as np
import statistics
import math

ra = 0.45   # resistencia del amperímetro (ohm)
rv = 10e6   # resistencia del voltímetro (ohm)
fuente_instru_v= 5e-2/math.sqrt(3) #[%]
fuente_instru_i= 8e-2/math.sqrt(3) #[%]
fuente_rv= 5 #[%]
fuente_ra= 5 #[%]

selector=0 #0 = TBM ; 1 = CBM

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
    media_v_tbm = statistics.mean(v_tbm)
    print("Media de V TBM =", media_v_tbm)
    
    media_r_tbm=media_v_tbm/media_i_tbm
    print("Media de R =", media_r_tbm)
    
    errorm_tbm= (-media_r_tbm)/rv
    errorm_tbm_porcentual=errorm_tbm*100
    rcorr_tbm=media_r_tbm/(1+errorm_tbm)
    
    desvio_i_tbm = statistics.stdev(i_tbm)
    desvio_v_tbm = statistics.stdev(v_tbm)

    rep_v_tbm = desvio_i_tbm/math.sqrt(len(i_tbm)) #TIPO A (Hacerla %)
    rep_i_tbm = desvio_v_tbm/math.sqrt(len(v_tbm)) #TIPO A (Hacerla %)
    
    cuenta_v_tbm=0/math.sqrt(3) #[%] // Calcularla
    cuenta_i_tbm=0/math.sqrt(3) #[%] // Calcularla
    
    Coef_sens_vind_tbm=1/(1-(media_r_tbm/rv))
    Coef_sens_iind_tbm=1/((media_r_tbm/rv)-1)
    Coef_sens_rind_tbm=1/(1-(rv/media_r_tbm))
    
    f_v=pow(Coef_sens_vind_tbm*rep_v_tbm,2)
    f_ins_v=pow(Coef_sens_vind_tbm*fuente_instru_v,2)
    f_cuenta_v=pow(Coef_sens_vind_tbm*cuenta_v_tbm,2)
    f_i=pow(Coef_sens_iind_tbm*rep_i_tbm,2)
    f_ins_i=pow(Coef_sens_iind_tbm*fuente_instru_i,2)
    f_cuenta_i=pow(Coef_sens_iind_tbm*cuenta_i_tbm,2)
    f_rv=pow(fuente_rv/math.sqrt(3),2)
    
    Uc= math.sqrt(f_v+f_ins_v+f_cuenta_v+f_i+f_ins_i+f_cuenta_i+f_rv)
    
    Vef = 5 #AGREGAR FORMULA
    
    if Vef >= 30:
        K=2
    else: 
        K=1.85
    
    U_exp = K * Uc

    print(f"R: {rcorr_tbm} ± {U_exp}")  
    
    
if selector == 1 :  
    pass
