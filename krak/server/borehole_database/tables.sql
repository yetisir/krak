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

CREATE TABLE corephotocorner (
	corner_id SERIAL NOT NULL, 
	top FLOAT NOT NULL, 
	"left" FLOAT NOT NULL, 
	PRIMARY KEY (corner_id)
);

CREATE TABLE core_photo_log (
	hash INTEGER NOT NULL, 
	borehole_id INTEGER NOT NULL, 
	depth_from FLOAT NOT NULL, 
	depth_to FLOAT NOT NULL, 
	path VARCHAR(1024) NOT NULL, 
	crop_corner_1 INTEGER NOT NULL, 
	crop_corner_2 INTEGER NOT NULL, 
	crop_corner_3 INTEGER NOT NULL, 
	crop_corner_4 INTEGER NOT NULL, 
	comments VARCHAR(1024), 
	PRIMARY KEY (hash, depth_from), 
	FOREIGN KEY(borehole_id) REFERENCES borehole (borehole_id), 
	FOREIGN KEY(crop_corner_1) REFERENCES corephotocorner (corner_id), 
	FOREIGN KEY(crop_corner_2) REFERENCES corephotocorner (corner_id), 
	FOREIGN KEY(crop_corner_3) REFERENCES corephotocorner (corner_id), 
	FOREIGN KEY(crop_corner_4) REFERENCES corephotocorner (corner_id)
);