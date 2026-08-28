from ingestion.download_urlhaus import main as run_ingestion
from bronze.raw_ingestions_of_files_to_bronze import main as run_bronze
from silver.transform_silver import main as run_silver
from enrichment.dns_resolution import main as run_dns_enrichment
from gold.load_gold import main as run_gold


def main():

    print("=" * 60)
    print("URLHaus Threat Intelligence ETL Pipeline")
    print("=" * 60)

    print("\n[1/5] INGESTION")
    run_ingestion()

    print("\n[2/5] BRONZE")
    run_bronze()

    print("\n[3/5] SILVER")
    run_silver()

    print("\n[4/5] DNS ENRICHMENT")
    run_dns_enrichment()

    print("\n[5/5] GOLD")
    run_gold()

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()