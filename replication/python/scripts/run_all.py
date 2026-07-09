#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from causal_spdes.core import heat_eigenvalues, noise_loadings
from causal_spdes.likelihood import simulate_exact_ou, profile_mle
from causal_spdes.targets import integrated_mode_variance
from causal_spdes.nonidentification import feedback_gauge_example

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'config'/'profiles.json'
RESULTS=ROOT/'results'

def run(profile: str, figures_only: bool=False):
    cfg=json.loads(CONFIG.read_text())[profile]
    RESULTS.joinpath('tables').mkdir(parents=True,exist_ok=True)
    RESULTS.joinpath('figures').mkdir(parents=True,exist_ok=True)
    RESULTS.joinpath('logs').mkdir(parents=True,exist_ok=True)
    start=time.time()
    rows=[]
    for N,n in cfg['designs']:
        lam=heat_eigenvalues(N); q=noise_loadings(lam,cfg['beta'])
        th=[]; sg=[]
        reps=cfg['reps'] if not figures_only else min(cfg['reps'],50)
        for r in range(reps):
            y=simulate_exact_ou(cfg['theta'],cfg['sigma'],lam,q,n,cfg['horizon'],cfg['seed']+100000*N+r)
            a,b=profile_mle(y,lam,q,cfg['horizon'])
            th.append(a); sg.append(b)
        Lambda=float(np.sum(lam))
        zt=np.sqrt(Lambda)*(np.array(th)-cfg['theta'])/np.sqrt(2*cfg['theta']/cfg['horizon'])
        zs=np.sqrt(N*n)*(np.array(sg)-cfg['sigma'])/(cfg['sigma']/np.sqrt(2))
        rows.append({'N':N,'n':n,'reps':reps,'theta_mean':np.mean(th),'sigma_mean':np.mean(sg),'z_theta_sd':np.std(zt,ddof=1),'z_sigma_sd':np.std(zs,ddof=1)})
    frame=pd.DataFrame(rows); frame.to_csv(RESULTS/'tables'/'estimation_summary.csv',index=False)
    plt.figure(figsize=(6.8,4.2)); plt.plot(frame.N,frame.z_theta_sd,marker='o',label=r'$Z_\theta$'); plt.plot(frame.N,frame.z_sigma_sd,marker='s',label=r'$Z_\sigma$'); plt.axhline(1,ls='--'); plt.xlabel('N'); plt.ylabel('Empirical standard deviation'); plt.legend(); plt.tight_layout(); plt.savefig(RESULTS/'figures'/'lan_scale_check.png',dpi=180); plt.close()
    rates=np.array([0.4,0.7,1.0,1.4,2.0]); vars_=integrated_mode_variance(rates,cfg['sigma'],1.0,cfg['horizon'])
    plt.figure(figsize=(6.8,4.2)); plt.plot(rates,vars_,marker='o'); plt.xlabel('Post-intervention rate'); plt.ylabel('Integrated-functional variance'); plt.tight_layout(); plt.savefig(RESULTS/'figures'/'counterfactual_variance_curve.png',dpi=180); plt.close()
    ni=feedback_gauge_example(); pd.DataFrame([ni]).to_csv(RESULTS/'tables'/'nonidentification_summary.csv',index=False)
    manifest={'profile':profile,'elapsed_seconds':time.time()-start,'config':cfg}
    (RESULTS/'logs'/'run_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(frame.to_string(index=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('profile',choices=['preview','standard','publication']); p.add_argument('--figures-only',action='store_true'); args=p.parse_args(); run(args.profile,args.figures_only)
