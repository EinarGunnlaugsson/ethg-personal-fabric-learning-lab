# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "2ce6d3c1-dc25-475c-bf31-e4e6b5df90af",
# META       "default_lakehouse_name": "Einars_lake",
# META       "default_lakehouse_workspace_id": "64c0f161-e476-4bf2-bb58-a2e2685f5f59",
# META       "known_lakehouses": [
# META         {
# META           "id": "2ce6d3c1-dc25-475c-bf31-e4e6b5df90af"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Delta Lake tables 
# Use this notebook to explore Delta Lake functionality 

# CELL ********************

 from pyspark.sql.types import StructType, IntegerType, StringType, DoubleType

 # define the schema
 schema = StructType() \
 .add("ProductID", IntegerType(), True) \
 .add("ProductName", StringType(), True) \
 .add("Category", StringType(), True) \
 .add("ListPrice", DoubleType(), True)

 df = spark.read.format("csv").option("header","true").schema(schema).load("Files/products/products.csv")
 # df now is a Spark DataFrame containing CSV data from "Files/products/products.csv".
 display(df)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

 df.write.format("delta").saveAsTable("managed_products")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df.write.format("delta").saveAsTable("external_products", path="abfss://Einar_ehf@onelake.dfs.fabric.microsoft.com/Einars_lake.Lakehouse/Files/new_external_products")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# MAGIC %%sql
# MAGIC CREATE EXTERNAL TABLE external_products
# MAGIC USING DELTA
# MAGIC LOCATION 'abfss://Einar_ehf@onelake.dfs.fabric.microsoft.com/Einars_lake.Lakehouse/Files/external_products';

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

 %%sql
 DESCRIBE FORMATTED managed_products;

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

 %%sql
 DESCRIBE FORMATTED external_products;

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

 %%sql
 DROP TABLE managed_products;

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

 %%sql
 CREATE TABLE products
 USING DELTA
 LOCATION 'Files/products';

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from notebookutils import mssparkutils
from pyspark.sql.types import *
from pyspark.sql.functions import *

# Create a folder
inputPath = 'Files/data/'
mssparkutils.fs.mkdirs(inputPath)

# Create a stream that reads data from the folder, using a JSON schema
jsonSchema = StructType([
StructField("device", StringType(), False),
StructField("status", StringType(), False)
])
iotstream = spark.readStream.schema(jsonSchema).option("maxFilesPerTrigger", 1).json(inputPath)

# Write some event data to the folder
device_data = '''{"device":"Dev1","status":"ok"}
{"device":"Dev1","status":"ok"}
{"device":"Dev1","status":"ok"}
{"device":"Dev2","status":"error"}
{"device":"Dev1","status":"ok"}
{"device":"Dev1","status":"error"}
{"device":"Dev2","status":"ok"}
{"device":"Dev2","status":"error"}
{"device":"Dev1","status":"ok"}'''

mssparkutils.fs.put(inputPath + "data.txt", device_data, True)

print("Source stream created...")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

 # Write the stream to a delta table
 delta_stream_table_path = 'Tables/iotdevicedata'
 checkpointpath = 'Files/delta/checkpoint'
 deltastream = iotstream.writeStream.format("delta").option("checkpointLocation", checkpointpath).start(delta_stream_table_path)
 print("Streaming to delta sink...")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

 %%sql
 SELECT * FROM IotDeviceData;

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

 # Add more data to the source stream
 more_data = '''{"device":"Dev1","status":"ok"}
 {"device":"Dev1","status":"ok"}
 {"device":"Dev1","status":"ok"}
 {"device":"Dev1","status":"ok"}
 {"device":"Dev1","status":"error"}
 {"device":"Dev2","status":"error"}
 {"device":"Dev1","status":"ok"}'''

 mssparkutils.fs.put(inputPath + "more-data.txt", more_data, True)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

 deltastream.stop()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
