### Tetation ISO Generator

This is the source code for https://tetration-iso-generator.io/

The project can be used to generate ISO configuration files used by Tetration to launch connector appliances.

### Running Locally

This repository is deployed as a hosted solution already.

If you wish to run a copy in yoour local environment, follow these steps.

You must have the package `mkisofs` installed. Please use your OS package manager.

```
git clone https://github.com/tetration-exchange/tetration-iso-generator.git

cd tetration-iso-generator/

pip install -r requirements.txt

export FLASK_APP=application.py

flask run
```

The application will then be serving requests at `http://127.0.0.1:5000`
