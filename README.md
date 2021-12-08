# SARP-DataVisBot
Ground data visualization program that works over IRC chat.

### How to configure
This program will run on a computer that has Python 3 installed.
You need to install the Python packages `pygame` and `matplotlib`.
On Windows computers, you can type `py -m pip install pygame matplotlib` in a command line.

**Logging in**
You need to change the name of the bot on the chat:
The following line is at the end of the program.
```python
client = IRCClient(
        "<website>",
        6668,
        "ENTER NAME HERE",
        "<password>",
        "#SARP2021"
    )
```

You can also change the variables that it measures:
```python
coll = DataCollector(
        ["CH4", "CO", "NOX", "HCHO", "O3"]
    )
```

The names are not case-sensitive.
