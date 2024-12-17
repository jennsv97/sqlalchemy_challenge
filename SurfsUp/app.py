import numpy as np
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
station_table = Base.classes.station
measurement_table = Base.classes.measurement

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

# Home route
@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Hawaii Climate Analysis API<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )

# Precipitation route
@app.route("/api/v1.0/precipitation", methods=["GET"])
def precipitation():
    """Retrieve the last 12 months of precipitation data."""
    # Query for the most recent date in the database
    recent_date = session.query(measurement_table.date).order_by(measurement_table.date.desc()).first()[0]
    
    # Calculate one year ago from the most recent date
    one_year_ago = dt.datetime.strptime(recent_date, "%Y-%m-%d") - dt.timedelta(days=365)

    # Query the precipitation data from the last 12 months
    query_prcp = session.query(measurement_table.date, measurement_table.prcp).\
        filter(measurement_table.date >= one_year_ago).all()

    # Convert the query results into a dictionary
    prcp_data = {date: prcp for date, prcp in query_prcp}
    
    return jsonify(prcp_data)

# Stations route
@app.route("/api/v1.0/stations", methods=["GET"])
def stations():
    """Return a JSON list of stations."""
    stations = session.query(station_table.station).all()
    station_list = [station[0] for station in stations]
    return jsonify(station_list)

# Temperature observations route
@app.route("/api/v1.0/tobs", methods=["GET"])
def tobs():
    """Retrieve temperature observations for the most active station and plot them."""
    # Get the most active station ID
    most_active_station_id = session.query(measurement_table.station)\
        .group_by(measurement_table.station)\
        .order_by(func.count(measurement_table.station).desc())\
        .first()[0]

    # Calculate one year ago from the most recent date
    recent_date = session.query(measurement_table.date).order_by(measurement_table.date.desc()).first()[0]
    one_year_ago = dt.datetime.strptime(recent_date, "%Y-%m-%d") - dt.timedelta(days=365)

    # Query temperature data for the last 12 months
    temp_data = session.query(measurement_table.tobs)\
        .filter(measurement_table.station == most_active_station_id)\
        .filter(measurement_table.date >= one_year_ago).all()

    # Convert to a Pandas DataFrame
    temp_df = pd.DataFrame(temp_data, columns=["Temperature"])

    # Create the histogram
    plt.hist(temp_df["Temperature"], bins=12)
    plt.xlabel("Temperature")
    plt.ylabel("Frequency")
    plt.title(f"Temperature Observations for Station {most_active_station_id}")

    # Save it to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    # Encode the image to base64
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    
    return jsonify({"image": img_base64})

# Temperature statistics for start date route
@app.route("/api/v1.0/<start>", methods=["GET"])
def start_temp_stats(start):
    """Return the min, avg, and max temperatures for a given start date."""
    stats = session.query(
        func.min(measurement_table.tobs).label("Min_Temperature"),
        func.avg(measurement_table.tobs).label("Avg_Temperature"),
        func.max(measurement_table.tobs).label("Max_Temperature")
    ).filter(measurement_table.date >= start).all()

    temperature_data = {"min": stats[0].Min_Temperature,
                        "avg": stats[0].Avg_Temperature,
                        "max": stats[0].Max_Temperature}
    
    return jsonify(temperature_data)

# Temperature statistics for start and end date route
@app.route("/api/v1.0/<start>/<end>", methods=["GET"])
def start_end_temp_stats(start, end):
    """Return the min, avg, and max temperatures for a given start-end date range."""
    stats = session.query(
        func.min(measurement_table.tobs).label("Min_Temperature"),
        func.avg(measurement_table.tobs).label("Avg_Temperature"),
        func.max(measurement_table.tobs).label("Max_Temperature")
    ).filter(measurement_table.date >= start).filter(measurement_table.date <= end).all()

    temperature_data = {"min": stats[0].Min_Temperature,
                        "avg": stats[0].Avg_Temperature,
                        "max": stats[0].Max_Temperature}
    
    return jsonify(temperature_data)

if __name__ == "__main__":
    app.run(debug=True)