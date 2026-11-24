"""Reproduce the 48-case small-current analytical benchmark."""
import argparse
from pathlib import Path
import pandas as pd
from solid_pinn.analytical import benchmark

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',default='outputs/v061_analytic_results.csv')
    args=parser.parse_args()
    result=pd.DataFrame(benchmark())
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    result.to_csv(path,index=False)
    print(result.groupby(['case','solver','nx']).max_reaction_error_pct.max().to_string())
