# Installation

## gcc compiler
```
source /opt/rh/devtoolset-2/enable
```

## Install pyenv
```
curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
PYTHON_CONFIGURE_OPTS="--enable-unicode=ucs4" pyenv install 2.7.11
```

## Install albula

Download and unpack the albula code from [dectris.com](https://www.dectris.com/albula.html)

```bash
./ALBULA-3.2.0-2-x86_64.sh --python=python --accept-license --prefix=$HOME/bin
```

## Install control module

```bash
python setup.py develop
```
