# bn-benchmarks

This repository contains Bayesian networks used in my experiments.
The networks are found in the `bayesian-networks` directory in BIF and UAI format.
Some networks come from [the bnlearn repository](https://www.bnlearn.com/about/); if you use them please use the appropriate citation:

```
@article{scutari2009learning,
  title={Learning Bayesian networks with the bnlearn R package},
  author={Scutari, Marco},
  journal={arXiv preprint arXiv:0908.3817},
  year={2009}
}
```

In the `scripts` directory you can find some utilities to computes marginal probabilities from UAI files, either using a WMC encodings
(references below) or with [ProbLog](https://dtai.cs.kuleuven.be/problog/)

## CNF encodings

### Weighted Model Counting

I use various encoding based on weighted model counting, and I use [this wonderful tool](https://www.cril.univ-artois.fr/software/bn2cnf/) coded by the [Cril](https://www.cril.univ-artois.fr/) to transform UAI-formatted bn into the appropriate CNF.
Currently, this repository contains the following encodings; if you use any of these, please cite the associated papers.

- ENC3
```
@inproceedings{chaviraCompilingBayesianNetworks2005,
  title = {Compiling {{Bayesian}} Networks with Local Structure},
  booktitle = {{{IJCAI}}},
  author = {Chavira, Mark and Darwiche, Adnan},
  year = {2005},
  volume = {5}
}
```
- ENC4
```
@inproceedings{chaviraEncodingCNFsEmpower2006,
  title = {Encoding {{CNFs}} to Empower Component Analysis},
  booktitle = {Theory and {{Applications}} of {{Satisfiability Testing-SAT}} 2006: 9th {{International Conference}}, {{Seattle}}, {{WA}}, {{USA}}, {{August}} 12-15, 2006. {{Proceedings}} 9},
  author = {Chavira, Mark and Darwiche, Adnan},
  year = {2006},
  publisher = {{Springer}}
}
```
- ENC4LINP
```
@inproceedings{bartImprovedCNFEncoding2016,
  title = {An Improved {{CNF}} Encoding Scheme for Probabilistic Inference},
  booktitle = {Proceedings of the {{Twenty-second European Conference}} on {{Artificial Intelligence}}},
  author = {Bart, Anicet and Koriche, Fr{\'e}d{\'e}ric and Lagniez, Jean-Marie and Marquis, Pierre},
  year = {2016}
}
```

### Projected Weighted Model Counting

For now, the only projected weighted model counting encoding is the one proposed in `Schlandals`.
- sch
```
@inproceedings{dubrayProbabilisticInferenceProjected2023a,
  title = {Probabilistic {{Inference}} by {{Projected Weighted Model Counting}} on {{Horn Clauses}}},
  author = {Dubray, Alexandre and Schaus, Pierre and Nijssen, Siegfried},
  year = {2023},
  publisher = {Schloss Dagstuhl -- Leibniz-Zentrum f{\"u}r Informatik},
  doi = {10.4230/LIPIcs.CP.2023.15},
}
```
