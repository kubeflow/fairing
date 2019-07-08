#!/usr/bin/env python
# coding: utf-8

# # Test Notebook

# fairing:include-cell
print('This cell includes fairing:include-cell')


if __name__ == "__main__":
  import fire
  import logging
  logging.basicConfig(format='%(message)s')
  logging.getLogger().setLevel(logging.INFO)
  fire.Fire(None)
