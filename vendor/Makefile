clean:
	@echo "Cleaning up existing vendor files ..."
	@rm -rf avro jansson

download: clean
	@echo "Downloading vendor files ..."
	@wget https://github.com/apache/avro/archive/release-1.8.0.tar.gz
	@wget https://github.com/akheron/jansson/archive/v2.7.tar.gz
	@mkdir avro && tar xzf release-1.8.0.tar.gz -C avro --strip-components 1
	@mkdir jansson && tar xzf v2.7.tar.gz -C jansson --strip-components 1
	@rm *.tar.gz
