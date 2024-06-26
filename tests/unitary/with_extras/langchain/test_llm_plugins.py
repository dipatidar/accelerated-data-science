#!/usr/bin/env python
# -*- coding: utf-8 -*--

# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

import pytest
import unittest
from unittest.mock import patch

from ads.llm import ModelDeploymentTGI
from oci.signer import Signer


class LangChainPluginsTest(unittest.TestCase):
    mock_endpoint = "https://mock_endpoint/predict"

    def mocked_requests_post(endpoint, headers, json, auth, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def raise_for_status(self):
                pass

        assert endpoint.startswith("https://")
        assert json
        assert headers
        prompt = json.get("inputs")
        assert prompt and isinstance(prompt, str)
        completion = "ads" if "who" in prompt else "Unknown"
        assert auth
        assert isinstance(auth, Signer)

        return MockResponse(
            json_data={"generated_text": completion},
            status_code=200,
        )

    def test_oci_model_deployment_model_param(self):
        llm = ModelDeploymentTGI(endpoint=self.mock_endpoint, temperature=0.9)
        model_params_keys = [
            "best_of",
            "max_new_tokens",
            "temperature",
            "top_k",
            "top_p",
            "do_sample",
            "return_full_text",
            "watermark",
        ]
        assert llm.endpoint == self.mock_endpoint
        assert all(key in llm._default_params for key in model_params_keys)
        assert llm.temperature == 0.9

    @patch("requests.post", mocked_requests_post)
    def test_oci_model_deployment_call(self):
        llm = ModelDeploymentTGI(endpoint=self.mock_endpoint)
        response = llm("who am i")
        completion = "ads"
        assert response == completion
