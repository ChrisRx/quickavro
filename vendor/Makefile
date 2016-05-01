clean:
	@echo "Cleaning up existing vendor files ..."
	@rm -rf avro jansson snappy zlib

download: clean
	@echo "Downloading vendor files ..."
	@wget https://github.com/apache/avro/archive/release-1.8.0.tar.gz -O avro-1.8.0.tar.gz
	@wget https://github.com/akheron/jansson/archive/v2.7.tar.gz -O jansson-2.7.tar.gz
	@wget https://github.com/google/snappy/releases/download/1.1.3/snappy-1.1.3.tar.gz -O snappy-1.1.3.tar.gz
	@wget https://github.com/madler/zlib/archive/v1.2.8.tar.gz -O zlib-1.2.8.tar.gz
	@mkdir avro && tar xzf avro-1.8.0.tar.gz -C avro --strip-components 1
	@mkdir jansson && tar xzf jansson-2.7.tar.gz -C jansson --strip-components 1
	@mkdir snappy && tar xzf snappy-1.1.3.tar.gz -C snappy --strip-components 1
	@mkdir zlib && tar xzf zlib-1.2.8.tar.gz -C zlib --strip-components 1
	@rm *.tar.gz
