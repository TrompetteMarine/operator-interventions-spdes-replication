#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import norm


def modal_constant_weight(lam, q, u0, c, a, horizon):
    x = a * lam * horizon
    mean = c * u0 * (-np.expm1(-x)) / (a * lam)
    bracket = horizon - 2.0 * (-np.expm1(-x)) / (a * lam) + (-np.expm1(-2.0 * x)) / (2.0 * a * lam)
    variance = q * q * c * c * bracket / (a * a * lam * lam)
    return mean, variance


def cdf_distance(m0, v0, m1, v1, sigma):
    sd0, sd1 = sigma * math.sqrt(v0), sigma * math.sqrt(v1)
    grid = np.linspace(min(m0 - 7*sd0, m1 - 7*sd1), max(m0 + 7*sd0, m1 + 7*sd1), 12001)
    return float(np.max(np.abs(norm.cdf((grid-m0)/sd0) - norm.cdf((grid-m1)/sd1))))


def slope_ci(x, y, tail=5):
    x = np.asarray(x, float)[-tail:]
    y = np.asarray(y, float)[-tail:]
    mask = (x > 0) & (y > 0)
    res = stats.linregress(np.log(x[mask]), np.log(y[mask]))
    crit = stats.t.ppf(0.975, max(int(mask.sum()) - 2, 1))
    return float(res.slope), float(res.slope - crit*res.stderr), float(res.slope + crit*res.stderr), float(res.rvalue**2)


def spatial_alpha(config, out_dir):
    can = config['canonical']; gal = config['galerkin']
    a, sigma, T = float(can['theta_intervention']), float(can['sigma0']), float(can['horizon'])
    r0, gamma = float(can['initial_exponent']), float(can['weight_exponent'])
    Kref = int(gal['reference_K'])
    k = np.arange(1, Kref+1, dtype=float)
    lam = np.pi**2*k**2
    u0 = lam**(-r0/2)
    weight = lam**(-gamma/2)
    rows=[]; slope_rows=[]
    for alpha in gal['alpha_q_values']:
        alpha=float(alpha); q=k**(-alpha)
        mm,vv=modal_constant_weight(lam,q,u0,weight,a,T)
        cm=np.cumsum(mm); cv=np.cumsum(vv); mf=float(cm[-1]); vf=float(cv[-1])
        local=[]
        for K in gal['K_values']:
            K=int(K); mk=float(cm[K-1]); vk=float(cv[K-1])
            mt=abs(mf-mk); vt=max(vf-vk,0.0)
            strong=math.sqrt(mt*mt + sigma*sigma*vt)
            w2=math.sqrt(mt*mt + sigma*sigma*(math.sqrt(vf)-math.sqrt(vk))**2)
            cdf=cdf_distance(mf,vf,mk,vk,sigma)
            row={'alpha_q':alpha,'K':K,'mean_error':mt,'variance_error':vt,'strong_rms':strong,'W2':w2,'cdf_sup':cdf}
            rows.append(row); local.append(row)
        df=pd.DataFrame(local)
        predictions={
            'mean_error':-(r0+gamma+1.0),
            'variance_error':-(2.0*alpha+2.0*gamma+3.0),
            'strong_rms':-min(r0+gamma+1.0, alpha+gamma+1.5),
            'W2':-min(r0+gamma+1.0, 2.0*alpha+2.0*gamma+3.0),
            'cdf_sup':-min(r0+gamma+1.0, 2.0*alpha+2.0*gamma+3.0),
        }
        for metric,pred in predictions.items():
            sl,lo,hi,r2=slope_ci(df['K'],df[metric])
            slope_rows.append({'alpha_q':alpha,'metric':metric,'predicted_slope':pred,'empirical_slope':sl,'ci_low':lo,'ci_high':hi,'r_squared':r2})
    frame=pd.DataFrame(rows); slopes=pd.DataFrame(slope_rows)
    frame.to_csv(out_dir/'galerkin_alpha_rates.csv',index=False)
    slopes.to_csv(out_dir/'galerkin_slope_summary.csv',index=False)
    plt.figure(figsize=(8.0,4.8))
    for alpha in gal['alpha_q_values']:
        sub=frame[frame.alpha_q==float(alpha)]
        plt.loglog(sub.K,sub.cdf_sup,marker='o',label=f'alpha_q={alpha}')
    plt.xlabel('Galerkin level K'); plt.ylabel('CDF sup error'); plt.title('Noise-smoothness sensitivity of Galerkin law error'); plt.legend(); plt.tight_layout()
    plt.savefig(out_dir.parent/'figures'/'galerkin_alpha_rates.png',dpi=210); plt.close()
    return frame,slopes


def balancing(config,out_dir):
    can=config['canonical']; theta=float(can['theta_intervention']); sigma=float(can['sigma0']); T=float(can['horizon']); alpha=float(can['alpha_q']); r0=float(can['initial_exponent']); gamma=float(can['weight_exponent'])
    Kref=500000; k=np.arange(1,Kref+1,dtype=float); lam=np.pi**2*k**2; q=k**(-alpha); u0=lam**(-r0/2); w=lam**(-gamma/2)
    mm,vv=modal_constant_weight(lam,q,u0,w,theta,T); cm=np.cumsum(mm); cv=np.cumsum(vv); mf=float(cm[-1]); vf=float(cv[-1]); z=mf+0.5*sigma*math.sqrt(vf); f0=float(norm.cdf((z-mf)/(sigma*math.sqrt(vf))))
    Kgrid=np.asarray([2,3,5,8,12,20,30,50,80,120,200,400]); rows=[]
    rho=r0+gamma+1.0
    for design in config['theorem_aligned_designs']:
        N,n=int(design['N']),int(design['n']); R=math.sqrt(N*n); stat_sd=abs(-0.5*norm.pdf(0.5)/sigma)*sigma/math.sqrt(2.0)/R
        biases=[]
        for K in Kgrid:
            mk=float(cm[K-1]); vk=float(cv[K-1]); fk=float(norm.cdf((z-mk)/(sigma*math.sqrt(vk)))); bias=abs(fk-f0); total=math.sqrt(stat_sd**2+bias**2)
            rows.append({'N':N,'n':n,'R_fast':R,'K':int(K),'truncation_bias':bias,'statistical_sd':stat_sd,'total_rmse_proxy':total,'bias_to_se':bias/stat_sd})
            biases.append(bias)
        sub=pd.DataFrame(rows)[lambda x:(x.N==N)&(x.n==n)]
        idx=int(np.argmin(np.abs(np.log(np.maximum(sub.bias_to_se.to_numpy(),1e-300)))))
        empirical=int(sub.iloc[idx].K); theoretical=max(2,int(round(R**(1.0/rho))))
        for row in rows[-len(Kgrid):]:
            row['empirical_balancing_K']=empirical; row['theoretical_balancing_K']=theoretical
    frame=pd.DataFrame(rows); frame.to_csv(out_dir/'combined_error_balancing.csv',index=False)
    plt.figure(figsize=(8.0,4.8))
    for N in sorted(frame.N.unique()):
        sub=frame[frame.N==N]
        plt.loglog(sub.K,sub.total_rmse_proxy,marker='o',label=f'N={N}')
    plt.xlabel('Galerkin level K'); plt.ylabel('Total RMSE proxy'); plt.title('Spatial bias approaching the statistical floor'); plt.legend(); plt.tight_layout()
    plt.savefig(out_dir.parent/'figures'/'combined_error_balancing.png',dpi=210); plt.close()
    return frame


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--config',type=Path,required=True); parser.add_argument('--root',type=Path,required=True); args=parser.parse_args()
    config=json.loads(args.config.read_text()); tables=args.root/'results'/'tables'; figures=args.root/'results'/'figures'; tables.mkdir(parents=True,exist_ok=True); figures.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter(); spatial_alpha(config,tables); balancing(config,tables)
    (args.root/'results'/'manifests'/'extended_numerics_runtime.json').write_text(json.dumps({'elapsed_seconds':time.perf_counter()-start},indent=2))

if __name__=='__main__': main()
