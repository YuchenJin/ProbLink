# ProbLink

## What is ProbLink?
ProbLink is a probabilistic AS relationship inference algorithm, which does inference based on key AS-interconnection features derived from stochastically informative signals. Learn more about ProbLink in our [NSDI paper](https://www.usenix.org/conference/nsdi19/presentation/jin).

## Quickstart
To get started using ProbLink, clone or download this [GitHub repo](https://github.com/YuchenJin/ProbLink).

__Install Python dependencies__
```sh
$ pip install --user -r requirements.txt
```

__Prepare BGP paths__

You can prepare BGP paths of your interest and save them to a file 'rib.txt'. The ASes on each BGP path should be delimited by '|' on each line, for example, AS1|AS2|AS3.
    
We provide a script (bgp_path_downloader.py) for downloading BGP paths collected from all route collectors in RouteViews and RIPE NCC towards IPv4 prefixes by using [BGPStream](https://bgpstream.caida.org/).
Follow the [instructions](https://bgpstream.caida.org/download) to install BGPStream V2 first and then install pybgpstream.

```sh
$ python bgp_path_downloader.py -s <start date> -d <duration (in seconds)>

# for example, to download BGP paths on 06/01/2019 from all available route collectors
$ python bgp_path_downloader.py -s 06/01/2019 -d 86400
# BGP paths are written to 'rib.txt'.
```

__Download AS to Organization Mapping Dataset from CAIDA__

https://www.caida.org/data/as-organizations/

__Download PeeringDB Dataset from CAIDA__

Before March 2016: http://data.caida.org/datasets/peeringdb-v1/
    
After March 2016: http://data.caida.org/datasets/peeringdb/

__Parse downloaded BGP paths__
```sh
$ python bgp_path_parser.py <peeringdb file> 
# Output is written to 'sanitized_rib.txt'.
```

__Run AS-Rank algorithm to bootstrap ProbLink__
```sh
$ ./asrank.pl sanitized_rib.txt > asrank_result.txt
```

__Run ProbLink__ 
```sh
$ python problink.py -p <peeringdb file> -a <AS to organization mapping file>
```

## Output data format
\<provider-as\>|\<customer-as\>|-1 

\<peer-as\>|\<peer-as\>|0 

\<sibling-as\>|\<sibling-as\>|1

## Contact 
+ [Yuchen Jin](https://yuchenjin.github.io/)

You can contact us at <yuchenj@cs.washington.edu>.

## Monthly inferred results
You may want to download the monthly inferred AS relationships [here](https://yuchenjin.github.io/problink-as-relationships/).
