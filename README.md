# logslice

Lightweight Python library for filtering and streaming structured log files with regex and time-range support.

---

## Installation

```bash
pip install logslice
```

---

## Usage

```python
from logslice import LogSlicer

slicer = LogSlicer("app.log")

# Filter by time range and regex pattern
results = slicer.filter(
    start="2024-01-15 08:00:00",
    end="2024-01-15 09:00:00",
    pattern=r"ERROR|CRITICAL"
)

for entry in results:
    print(entry)

# Stream a large log file without loading it fully into memory
for entry in slicer.stream(pattern=r"timeout"):
    print(entry)
```

### CLI

```bash
logslice app.log --start "2024-01-15 08:00:00" --end "2024-01-15 09:00:00" --pattern "ERROR"
```

---

## Features

- 🔍 Regex-based log filtering
- ⏱️ Time-range queries on structured timestamps
- 📡 Memory-efficient streaming for large log files
- 🧩 Works with JSON, plaintext, and common log formats

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.