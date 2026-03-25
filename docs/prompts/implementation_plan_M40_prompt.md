Milestone 40: Synthetic Data Pipeline (ETL)

Objective

To transform the factory into a visual synthetic data generator. We will introduce new Source and Sink entities that read schemas from the YAML configuration, and a new Engine type that allows Factories to mutate data mid-flight using the faker Python library.

Prerequisite

Run pip install faker in the virtual environment.

1. The Faker Source (entities/faker_source.py)

Role (Extract): Replaces the standard DataSource. Instead of generating empty bouncy balls, it acts as a synthetic record generator.

YAML Configuration: It reads a faker_schema property (a dictionary mapping payload keys to Faker provider methods).

Example: {"first_name": "first_name", "email": "email", "ip": "ipv4"}

Logic: Every time its emit_timer triggers, it instantiates a Faker object, resolves the schema methods, and injects the resulting data dictionary into the PayloadBallPart before dropping it into the factory.

2. The Faker Factory Engine (utils/engines.py)

Role (Transform/Enrich): You were right—the Factory should act as a data mutator! We will add a new FakerEngine to the central engines file.

YAML Configuration: It reads a schema of fields to add or overwrite.

Example: {"job_title": "job", "email": "company_email"}

Logic: When a ball enters the Factory, the FakerEngine evaluates the schema. If a key already exists in the payload, it overwrites it. If it doesn't exist, it adds it. It then routes the ball forward using a standard success state (e.g., 10).

3. The File Sink (entities/file_sink.py)

Role (Load): Replaces the standard DataSink. Instead of just destroying the payload, it acts as a data exporter.

YAML Configuration: Reads output_directory (e.g., "exports/synthetic_data/") and file_format (e.g., "json").

Logic: When it ingests a payload, it dumps the payload's dictionary into a uniquely named file in the specified directory before destroying the ball. It automatically manages directory creation.

4. Advanced Enhancements (Suggestions)

To elevate this from a basic generator to an enterprise-grade ETL visualizer, consider implementing these additional features:

Batch Writing (Performance): Writing a new .json file for every single ball will quickly clutter the operating system. Add a batch_size property (e.g., 100) to the FileSink. It holds payloads in memory until it hits 100, then writes a single batch_timestamp.json containing an array of all 100 records.

CSV Support: Most data pipelines run on CSVs. If the FileSink's file_format is set to "csv", it should read the dictionary keys of the very first payload it receives to generate the CSV headers, and append subsequent payloads as rows.

Deterministic Seeds: Add a random_seed property to the FakerSource. By setting a specific integer seed, the Faker library will generate the exact same sequence of names and IPs every time you press PLAY. This is crucial for consistent testing.

The "Chaos Corruptor": Add a small chance (e.g., corruption_rate: 0.05) in the FakerSource to intentionally generate "bad" data (like null fields, missing keys, or numbers instead of strings). This forces the player to build Guard nodes and RuleEngine factories to catch and route bad data before it hits the Sink!