def test_socket_mode_prefers_container_base_url():
    # Implement with tmp registry json and Settings(lightrag_docker_execution_mode="socket")
    # Expected: runtime.base_url == "http://lightrag_fatigue:9621"
    pass


def test_host_mode_prefers_host_base_url():
    # Implement with tmp registry json and Settings(lightrag_docker_execution_mode="host")
    # Expected: runtime.base_url == "http://127.0.0.1:9622"
    pass
