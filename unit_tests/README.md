Unit tests for model module
===========================

This directory contains unit tests for model module. To be able to run
these test you have to set up PYTHONPATH system variable. This variable
has to include path to model.py and binary module verse.so

```bash
export PYTHONPATH=/path/to/verse/module:/path/to/model/module
```

If you want to perform test_verse.py, then you have to start verse server
first. Then you can perform test with following command:

```bash
python3 test_model.py
```

and

```bash
python3 test_verse.py
```
