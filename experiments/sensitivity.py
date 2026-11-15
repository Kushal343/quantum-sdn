"""One-factor optical sensitivity study of the analytical model."""
from dataclasses import replace
from pathlib import Path
import pandas as pd
from qkd_sdn.physics import Channel, Decoy, expected


def main():
    baseline = Channel()
    ranges = dict(distance_km=[10,20,40,60,80], detector_efficiency=[.05,.1,.2,.4],
                  dark_probability=[1e-6,2e-5,1e-4,1e-3], traffic=[0,.2,1,4,8],
                  misalignment=[.005,.015,.03,.05])
    rows = []
    for parameter, values in ranges.items():
        for value in values:
            qber, rate = expected(Decoy(), replace(baseline, **{parameter:value}))
            rows.append(dict(parameter=parameter,value=value,qber=qber,estimated_bits_per_second=rate))
    out = Path('results/sensitivity')
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out/'analytical.csv', index=False)


if __name__ == '__main__':
    main()
