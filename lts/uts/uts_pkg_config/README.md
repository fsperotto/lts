## Unsupervised Text Segmentation

https://github.com/intfloat/uts


### Install

For ```python 2.x```:

    sudo pip install uts

For ```python 3.x```:

    sudo pip3 install uts

### Usage

```python
import uts

document = ['this is a good day', 'good day means good weather',\
            'I love computer science', 'computer science is cool']
model = uts.C99(window=2)
boundary = model.segment(document)
# output: [1, 0, 1, 0]
print(boundary)
```
