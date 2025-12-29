"""CLI entry point for P6 Database Analyzer."""

import click
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_factory import DatabaseFactory
from analyzers.schema_health import SchemaHealthScanner
from analyzers.index_fragmentation import IndexFragmentationChecker
from analyzers.table_analyzer import TableAnalyzer
from analyzers.corruption_detector import CorruptionDetector
from utils.logging_config import setup_logging
from utils.credential_manager import get_credential_manager

# Initialize logging
logger = setup_logging()


@click.group()
def cli():
    """P6 Database Analyzer CLI."""
    pass


@cli.command()
@click.option('--db-type', type=click.Choice(['oracle', 'mssql']), required=True)
@click.option('--host', required=True)
@click.option('--port', type=int)
@click.option('--service', required=True)
@click.option('--username', required=True)
@click.option('--password', prompt=True, hide_input=True)
@click.option('--profile', help='Use saved connection profile')
@click.option('--output', type=click.Path(), help='Output file for results')
def analyze(
    db_type,
    host,
    port,
    service,
    username,
    password,
    profile,
    output
):
    """Run database analysis."""
    try:
        # Load profile if specified
        if profile:
            cred_manager = get_credential_manager()
            profile_data = cred_manager.load_connection_profile(profile)
            db_type = profile_data.get('db_type', db_type)
            host = profile_data.get('host', host)
            port = profile_data.get('port', port)
            service = profile_data.get('service', service)
            username = profile_data.get('username', username)
            password = profile_data.get('password', password)
        
        # Set default ports
        if not port:
            port = 1521 if db_type == 'oracle' else 1433
        
        # Create connector
        if db_type == 'oracle':
            connector = DatabaseFactory.create_connector(
                'oracle',
                host=host,
                port=port,
                service_name=service,
                username=username,
                password=password
            )
        else:
            connector = DatabaseFactory.create_connector(
                'mssql',
                server=host,
                database=service,
                username=username,
                password=password
            )
        
        connector.connect()
        click.echo("Connected to database")
        
        # Run analyses
        results = {}
        
        click.echo("Running schema health scan...")
        scanner = SchemaHealthScanner(connector)
        results['schema_health'] = scanner.scan_schema_health()
        
        click.echo("Checking index fragmentation...")
        checker = IndexFragmentationChecker(connector)
        results['index_fragmentation'] = checker.check_fragmentation()
        
        click.echo("Analyzing tables...")
        analyzer = TableAnalyzer(connector)
        results['table_analysis'] = analyzer.analyze_tables()
        
        click.echo("Detecting corruption...")
        detector = CorruptionDetector(connector)
        results['corruption'] = detector.detect_issues()
        
        # Output results
        if output:
            import json
            with open(output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            click.echo(f"Results saved to {output}")
        else:
            click.echo("\nAnalysis Results:")
            click.echo(f"Schema Health: {results['schema_health'].get('status', 'unknown')}")
            click.echo(f"Index Fragmentation: {results['index_fragmentation'].get('status', 'unknown')}")
            click.echo(f"Table Analysis: {results['table_analysis'].get('status', 'unknown')}")
            click.echo(f"Corruption: {results['corruption'].get('status', 'unknown')}")
        
        connector.disconnect()
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--name', required=True)
@click.option('--db-type', type=click.Choice(['oracle', 'mssql']), required=True)
@click.option('--host', required=True)
@click.option('--port', type=int)
@click.option('--service', required=True)
@click.option('--username', required=True)
@click.option('--password', prompt=True, hide_input=True)
def save_profile(name, db_type, host, port, service, username, password):
    """Save a connection profile."""
    try:
        cred_manager = get_credential_manager()
        cred_manager.save_connection_profile(
            name, db_type, host, port or (1521 if db_type == 'oracle' else 1433),
            service, username, password
        )
        click.echo(f"Profile '{name}' saved")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def list_profiles():
    """List saved connection profiles."""
    try:
        cred_manager = get_credential_manager()
        profiles = cred_manager.list_profiles()
        if profiles:
            click.echo("Saved profiles:")
            for profile in profiles:
                click.echo(f"  - {profile}")
        else:
            click.echo("No profiles found")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()

