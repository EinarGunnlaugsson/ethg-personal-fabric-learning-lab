# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "387b0c69-2362-4536-b2eb-0215aa928ae7",
# META       "default_lakehouse_name": "mbl_fasteignir",
# META       "default_lakehouse_workspace_id": "64c0f161-e476-4bf2-bb58-a2e2685f5f59",
# META       "known_lakehouses": [
# META         {
# META           "id": "387b0c69-2362-4536-b2eb-0215aa928ae7"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# Welcome to your new notebook
# Type here in the cell editor to add code!


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import requests
from bs4 import BeautifulSoup
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType

# Initialize Spark Session
spark = SparkSession.builder.appName("RealEstateScraper").getOrCreate()

# Define URL
url = "https://www.mbl.is/fasteignir/"

def fetch_page(url):
    """Fetches the HTML content of the given URL."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(f"❌ Error fetching page: {response.status_code}")
        return None

def parse_listings(html):
    """Parses the HTML and extracts listings with title, price, and address."""
    soup = BeautifulSoup(html, "html.parser")
    listings = []

    # Find all property listings
    for listing_div in soup.find_all("div", class_="MuiCardContent-root jss255"):
        try:
            # Extract title (property name)
            title_tag = listing_div.find("h6", class_="MuiTypography-h6")
            title = title_tag.get_text(strip=True) if title_tag else "No title"

            # Extract listing link
            link_tag = listing_div.find("a", class_="jss262")
            link = f"https://www.mbl.is{link_tag['href']}" if link_tag else "No link"

            # Extract location (neighborhood)
            location_tag = listing_div.find("h6", class_="MuiTypography-subtitle1")
            location = location_tag.get_text(strip=True) if location_tag else "No location"

            # Extract additional details (Type, Size, Rooms, Bedrooms)
            details = listing_div.find_all("h6", class_="MuiTypography-subtitle1")
            property_type = size = rooms = bedrooms = "N/A"
            for detail in details:
                text = detail.get_text(strip=True)
                if "Tegund:" in text:
                    property_type = text.replace("Tegund:", "").strip()
                elif "Stærð:" in text:
                    size = text.replace("Stærð:", "").strip()
                elif "Herbergi:" in text:
                    rooms = text.replace("Herbergi:", "").strip()
                elif "Svefnherbergi:" in text:
                    bedrooms = text.replace("Svefnherbergi:", "").strip()

            # Extract price from <div class="MuiCardActions-root jss266">
            price_div = listing_div.find_next("div", class_="MuiCardActions-root jss266")
            price_tag = price_div.find("h6", class_="MuiTypography-h6") if price_div else None
            price = price_tag.get_text(strip=True) if price_tag else "No price"

            # Store extracted data
            listings.append((title, location, property_type, size, rooms, bedrooms, price, link))

        except Exception as e:
            print("⚠ Failed to parse a listing:", e)

    return listings

# 🟢 Fetch and parse data
html_content = fetch_page(url)
if html_content:
    listings_data = parse_listings(html_content)

    # ✅ Debug Step 1: Print extracted listings
    print("✅ Extracted Listings:", listings_data[:5])  # Show first 5 results

    # ✅ Debug Step 2: Check if we actually scraped anything
    if not listings_data:
        print("⚠ No data extracted! Check if the website's structure has changed.")

    # Define PySpark Schema
    schema = StructType([
        StructField("Title", StringType(), True),
        StructField("Location", StringType(), True),
        StructField("Property_Type", StringType(), True),
        StructField("Size", StringType(), True),
        StructField("Rooms", StringType(), True),
        StructField("Bedrooms", StringType(), True),
        StructField("Price", StringType(), True),
        StructField("Link", StringType(), True)
    ])

    # ✅ Convert extracted data into a PySpark DataFrame (only if there is data)
    if listings_data:
        df = spark.createDataFrame(listings_data, schema=schema)

        # ✅ Debug Step 3: Check DataFrame count
        print(f"✅ DataFrame Row Count: {df.count()}")

        # ✅ Debug Step 4: Show extracted data
        df.show(truncate=False)

        # ✅ Save to Delta Table in Fabric Lakehouse (overwrite old data)
        df.write.format("delta").mode("overwrite").saveAsTable("dbo.mbl_fasteignir")

        print("✅ Data successfully saved to Fabric Lakehouse as a Delta Table!")

        # ✅ Debug Step 5: Verify Delta Table
        df_check = spark.read.format("delta").load("mbl_fasteignir")
        df_check.show()

    else:
        print("⚠ No data available to store in the DataFrame.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Load the table from Fabric
df = spark.read.format("delta").load("Tables/mbl_fasteignir")

# Show the first few records
df.show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df.count()  # Check how many rows exist in the DataFrame

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
