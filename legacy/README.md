# Legacy monolithic script

The file `legacy/oos_uploader_southnotary.py` is a compatibility wrapper.

All business logic now lives in the `southnotary_uploader` package. Use one of:

```bash
python -m southnotary_uploader
python main.py
python legacy/oos_uploader_southnotary.py
```

For architecture and migration notes, see `docs/ARCHITECTURE.md`.
