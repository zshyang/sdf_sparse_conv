# Deep Learning on SDF for Classifying Brain Biomarkers

## To reproduce the results from paper, do the following steps,

- install `pytorch` and `sparceconov` locally

The website for sparse convolution is [here](https://github.com/traveller59/spconv)

- Download the processed dataset from [here](https://drive.google.com/file/d/19LrBrQCKtYJGh-ydfbU4N-SY3-YkuKxA/view?usp=sharing) and unzip it.

You would have a folder structure like the following:
```
.
+-- data
+-- src
+-- readme.md
+-- data.zip
```

- Run the srcipt with.
```bash
cd src
./sh/ad/train00.sh
```

Try different script in the folder `sh` to reproduce the results in the paper.

