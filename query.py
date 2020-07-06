import sparql

# https://stackoverflow.com/questions/35569042/ssl-certificate-verify-failed-with-python3
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


def get_province_for(latitude, longitude):

    q = """
    PREFIX italy: <http://localhost:8000/italy.ttl#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

    select ?closest_prov ?closest_region bif:st_distance(bif:st_point(""" + str(latitude) + ", " + str(longitude) + """), bif:st_point(?latitude, ?longitude)) as ?dist
    where {
        ?closest_prov rdf:type italy:Province ;
                      geo:lat ?latitude ;
                      geo:long ?longitude .
        ?closest_region italy:has_province ?closest_prov .
    } 
    order by ?dist
    limit 1
    """

    return sparql.unpack_row(sparql.query('http://localhost:8890/sparql', q).fetchall()[0])


def get_station_for(latitude, longitude):

    q = """
    PREFIX italy: <http://localhost:8000/italy.ttl#>
    PREFIX airbase: <http://reference.eionet.europa.eu/airbase/schema/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX pol: <http://localhost:8000/pollution.ttl#>
    PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
    PREFIX sk: <http://www.w3.org/2004/02/skos/core#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>

    select distinct(?internal_stat) ?dist
    where {
        service <https://semantic.eea.europa.eu/sparql> {
            select distinct(?stat) bif:st_distance(bif:st_point(""" + str(latitude) + ", " + str(longitude) + """), bif:st_point(?s_lat, ?s_long)) as ?dist
            where {
                ?stat rdf:type airbase:Station ;
                      geo:lat ?s_lat ;
                      geo:long ?s_long ;
                      airbase:country ?nation .
                ?nation sk:notation ?nation_code .
                filter(?nation_code='IT') .
            }
        }

        ?internal_stat owl:sameAs ?stat ;
                       pol:measures ?blank .
        ?blank pol:pollutant ?pollutant .
        ?pollutant pol:air_pollutant "PM10" . 
    }
    order by asc(?dist)
    limit 1
    """

    return sparql.unpack_row(sparql.query('http://localhost:8890/sparql', q).fetchall()[0])


def get_observations_for(province, station):
    q = """
    PREFIX italy: <http://localhost:8000/italy.ttl#>
    PREFIX obs: <http://localhost:8000/observation.ttl#>
    PREFIX dpc: <http://localhost:8000/dpc.ttl#>
    PREFIX pol: <http://localhost:8000/pollution.ttl#>
    PREFIX mob: <http://localhost:8000/mobility.ttl#>
    PREFIX airbase: <http://reference.eionet.europa.eu/airbase/schema/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
    PREFIX sk: <http://www.w3.org/2004/02/skos/core#>

    select ?date ?PM10 ?total_cases ?driving ?retail_recreation ?grocery_pharmacy ?parks ?transit_stations ?workplaces ?residential
    where {
        ?observation obs:date ?date ; 
                     obs:of ?p, 
                            ?r, 
                            ?s .

        ?p rdf:type dpc:DpcObservation ;
           dpc:place ?prov ;
           dpc:total_cases ?total_cases .
        ?prov rdf:type italy:Province ;
              italy:name ?province .
        filter (?prov = <http://localhost:8000/province/Ferrara>) .

        ?r rdf:type mob:MobilityObservation ;
           mob:place ?reg .
        ?reg rdf:type italy:Region ;
             italy:name ?region ;
             italy:has_province ?prov .
        optional { 
            ?r mob:driving ?driving ;
               mob:retail_recreation ?retail_recreation ;
               mob:grocery_pharmacy ?grocery_pharmacy ;
               mob:parks ?parks;
               mob:transit_stations ?transit_stations;
               mob:workplaces ?workplaces ;
               mob:residential ?residential .
        } 

        ?s rdf:type pol:PollutionObservation ;
           pol:Station <http://localhost:8000/station/IT0187A> .
        { 
            select ?m_observation avg(?concentration) as ?PM10
                where {
                    ?m_observation obs:of ?m_s .
                    
                    ?m_s rdf:type pol:PollutionObservation ;
                         pol:observing ?observing .

                    ?observing rdf:type pol:PollutantObservation ;
                               pol:pollutant ?pollutant ;
                               pol:pollutant_measurement ?measurement .

                    ?pollutant pol:air_pollutant "PM10" .
                    ?measurement pol:concentration ?concentration .
                } 
                group by ?m_observation
        }
        filter(?observation = ?m_observation) .

    } order by asc(?date)
    """

    return sparql.query('http://localhost:8890/sparql', q)
