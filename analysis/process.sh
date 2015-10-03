
cut -d ' ' -f 2 ../data/filtered_stats/valids.txt > valid_originals.txt
echo "extracting cacheable bytes"
./har_processing/extract_cacheable_bytes.rb valid_originals.txt | sort | uniq > cacheable_bytes.dat
echo "extracting plt"
./har_processing/extract_plt.rb valid_originals.txt > replay_plts.dat
egrep '.pc.har ' replay_plts.dat > perfect_cache_replay_plts.dat
egrep -v '.pc.har ' replay_plts.dat > unmodified_replay_plts.dat

./graphs/percent_plt_reduction/compute_median_reduction.rb replay_plts.dat > median_plt_reduction.dat 2>plt_got_worse.dat
./graphs/ratio_bytes_to_reduction/compute_ratio.rb  median_plt_reduction.dat cacheable_bytes.dat > ratio.dat


echo "Generating CDFs"
cd ./graphs/cacheable_bytes/; ./generate_cdf_from_raw_data.sh ../../cacheable_bytes.dat
cd ../../
echo "here1"
cd ./graphs/plts/; ./generate_cdf_from_raw_data.sh ../../unmodified_replay_plts.dat ../../perfect_cache_replay_plts.dat
cd ../../
echo "here2"
cd ./graphs/percent_plt_reduction/; ./generate_cdf_from_raw_data.sh ../../median_plt_reduction.dat
cd ../../
echo "here3"
cd ./graphs/ratio_bytes_to_reduction/; ./generate_cdf_from_raw_data.sh ../../ratio.dat
cd ../../
