# Blueprints

Each car folder holds `calib.json`: the image name, scale (px/m), origin and axis mapping of every view.
The blueprint images themselves are third-party drawings and are not committed. Put the image next to
its `calib.json` (file name as in `calib.json` → `image`) to run `pipeline/bp_check.py <car>`.

| Car | Source drawing |
|---|---|
| mazda2_2013 | 4-view line blueprint (Mazda 2 DE hatch) |
| civic_fd_2008 | Outlines — Honda Civic Sedan US 2006 |
| cx5_2020 | 4-view line blueprint (CX-5 KF) |
| mini_f55_2018 | vector-templates.com — MINI Cooper S 5-door 2018 |
| ranger_raptor_2019 | Ford Ranger Raptor 2019 vector blueprint |
