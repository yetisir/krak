-- Automatically generated queries from tables.py
CREATE TABLE borehole (
	borehole_id SERIAL NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	easting FLOAT NOT NULL, 
	northing FLOAT NOT NULL, 
	elevation FLOAT NOT NULL, 
	PRIMARY KEY (borehole_id)
);

CREATE TABLE survey (
	borehole_id INTEGER, 
	depth FLOAT NOT NULL, 
	survey_id SERIAL NOT NULL, 
	azimuth FLOAT NOT NULL, 
	dip FLOAT NOT NULL, 
	PRIMARY KEY (survey_id), 
	FOREIGN KEY(borehole_id) REFERENCES borehole (borehole_id)
);

CREATE TABLE lithology (
	lithology_id SERIAL NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	PRIMARY KEY (lithology_id)
);

CREATE TABLE lithology_log (
	borehole_id INTEGER NOT NULL, 
	depth_from FLOAT NOT NULL, 
	depth_to FLOAT NOT NULL, 
	lithology_id INTEGER NOT NULL, 
	comments VARCHAR(1024), 
	PRIMARY KEY (borehole_id, depth_from), 
	FOREIGN KEY(borehole_id) REFERENCES borehole (borehole_id), 
	FOREIGN KEY(lithology_id) REFERENCES lithology (lithology_id)
);

CREATE TABLE core_photo_log (
	borehole_id INTEGER NOT NULL, 
	depth_from FLOAT NOT NULL, 
	depth_to FLOAT NOT NULL, 
	path VARCHAR(1024) NOT NULL, 
	comments VARCHAR(1024), 
	PRIMARY KEY (borehole_id, depth_from), 
	FOREIGN KEY(borehole_id) REFERENCES borehole (borehole_id)
);