#!/usr/bin/env python
# Copyright (c) 2024 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

from dataclasses import dataclass
from urllib.parse import urlparse

from tornado.web import HTTPError

from ads.aqua.common.decorator import handle_exceptions
from ads.aqua.common.enums import Tags
from ads.aqua.constants import PRIVATE_ENDPOINT_TYPE
from ads.aqua.extension.base_handler import AquaAPIhandler
from ads.aqua.extension.errors import Errors
from ads.aqua.extension.utils import validate_function_parameters
from ads.aqua.model.entities import ImportModelDetails
from ads.aqua.ui import AquaUIApp
from ads.config import COMPARTMENT_OCID, IS_BYOR_ENABLED


@dataclass
class CLIDetails:
    """Interface to capture payload and command details for generating ads cli command"""

    command: str
    subcommand: str
    payload: dict


class AquaUIHandler(AquaAPIhandler):
    """
    Handler for Aqua UI REST APIs.

    Methods
    -------
    get(self, id="")
        Routes the request to fetch log groups, log ids details or compartments
    list_log_groups(self, id: str)
        Reads the AQUA deployment information.
    list_logs(self, log_group_id: str, **kwargs)
        Lists the specified log group's log objects.
    list_compartments(self, **kwargs)
        Lists the compartments in a compartment specified by ODSC_MODEL_COMPARTMENT_OCID env variable.

    Raises
    ------
    HTTPError: For various failure scenarios such as invalid input format, missing data, etc.
    """

    @handle_exceptions
    def get(self, id=""):
        """Handle GET request."""
        url_parse = urlparse(self.request.path)
        paths = url_parse.path.strip("/")
        if paths.startswith("aqua/logging"):
            if not id:
                return self.list_log_groups()
            return self.list_logs(id)
        elif paths.startswith("aqua/compartments/default"):
            return self.get_default_compartment()
        elif paths.startswith("aqua/compartments"):
            return self.list_compartments()
        elif paths.startswith("aqua/experiment"):
            return self.list_experiments()
        elif paths.startswith("aqua/versionsets"):
            return self.list_model_version_sets()
        elif paths.startswith("aqua/buckets"):
            return self.list_buckets()
        elif paths.startswith("aqua/job/shapes"):
            return self.list_job_shapes()
        elif paths.startswith("aqua/modeldeployment/shapes"):
            return self.list_model_deployment_shapes()
        elif paths.startswith("aqua/vcn"):
            return self.list_vcn()
        elif paths.startswith("aqua/subnets"):
            return self.list_subnets()
        elif paths.startswith("aqua/privateendpoints"):
            return self.list_private_endpoints()
        elif paths.startswith("aqua/shapes/limit"):
            return self.get_shape_availability()
        elif paths.startswith("aqua/bucket/versioning"):
            return self.is_bucket_versioned()
        elif paths.startswith("aqua/containers"):
            return self.list_containers()
        elif paths.startswith("aqua/capacityreservations/enabled"):
            return self.is_capacity_reservations_enabled()
        elif paths.startswith("aqua/capacityreservations"):
            return self.list_capacity_reservations()
        else:
            raise HTTPError(400, f"The request {self.request.path} is invalid.")

    @handle_exceptions
    def delete(self, id=""):
        """Handles DELETE request for clearing cache"""
        # todo: added for dev work, to be deleted if there's no feature to refresh cache in Aqua
        url_parse = urlparse(self.request.path)
        paths = url_parse.path.strip("/")
        if paths.startswith("aqua/compartments/cache"):
            return self.finish(AquaUIApp().clear_compartments_list_cache())
        else:
            raise HTTPError(400, f"The request {self.request.path} is invalid.")

    def list_log_groups(self, **kwargs):
        """Lists all log groups for the specified compartment or tenancy."""
        compartment_id = self.get_argument("compartment_id", default=COMPARTMENT_OCID)
        return self.finish(
            AquaUIApp().list_log_groups(compartment_id=compartment_id, **kwargs)
        )

    def is_capacity_reservations_enabled(self):
        """Checks if the tenant is whitelisted for BYOR (Bring your own reservation) feature."""
        return self.finish({"status": str(IS_BYOR_ENABLED).strip().lower() == "true"})

    def list_capacity_reservations(self, **kwargs):
        """Lists users compute reservations in a specified compartment."""
        compartment_id = self.get_argument("compartment_id", default=COMPARTMENT_OCID)
        return self.finish(
            AquaUIApp().list_capacity_reservations(
                compartment_id=compartment_id, **kwargs
            )
        )

    def list_logs(self, log_group_id: str, **kwargs):
        """Lists the specified log group's log objects."""
        return self.finish(AquaUIApp().list_logs(log_group_id=log_group_id, **kwargs))

    def list_compartments(self):
        """Lists the compartments in a compartment specified by ODSC_MODEL_COMPARTMENT_OCID env variable."""
        return self.finish(AquaUIApp().list_compartments())

    def list_containers(self):
        """Lists the AQUA containers."""
        return self.finish(AquaUIApp().list_containers())

    def get_default_compartment(self):
        """Returns user compartment ocid."""
        return self.finish(AquaUIApp().get_default_compartment())

    def list_model_version_sets(self, **kwargs):
        """Lists all model version sets for the specified compartment or tenancy."""

        compartment_id = self.get_argument("compartment_id", default=COMPARTMENT_OCID)
        return self.finish(
            AquaUIApp().list_model_version_sets(
                compartment_id=compartment_id,
                target_tag=Tags.AQUA_FINE_TUNING,
                **kwargs,
            )
        )

    def list_experiments(self, **kwargs):
        """Lists all experiments for the specified compartment or tenancy."""

        compartment_id = self.get_argument("compartment_id", default=COMPARTMENT_OCID)
        return self.finish(
            AquaUIApp().list_model_version_sets(
                compartment_id=compartment_id,
                target_tag=Tags.AQUA_EVALUATION,
                **kwargs,
            )
        )

    def list_buckets(self, **kwargs):
        """Lists all model version sets for the specified compartment or tenancy."""
        compartment_id = self.get_argument("compartment_id", default=COMPARTMENT_OCID)
        versioned = self.get_argument("versioned", default=None)
        versioned = True if versioned and versioned.lower() == "true" else False

        return self.finish(
            AquaUIApp().list_buckets(
                compartment_id=compartment_id, versioned=versioned, **kwargs
            )
        )

    def list_job_shapes(self, **kwargs):
        """Lists job shapes available in the specified compartment."""
        compartment_id = self.get_argument("compartment_id", default=COMPARTMENT_OCID)
        return self.finish(
            AquaUIApp().list_job_shapes(compartment_id=compartment_id, **kwargs)
        )

    def list_model_deployment_shapes(self, **kwargs):
        """Lists model deployment shapes available in the specified compartment."""
        compartment_id = self.get_argument("compartment_id", default=COMPARTMENT_OCID)
        return self.finish(
            AquaUIApp().list_model_deployment_shapes(
                compartment_id=compartment_id, **kwargs
            )
        )

    def list_vcn(self, **kwargs):
        """Lists the virtual cloud networks (VCNs) in the specified compartment."""
        compartment_id = self.get_argument("compartment_id", default=COMPARTMENT_OCID)
        return self.finish(
            AquaUIApp().list_vcn(compartment_id=compartment_id, **kwargs)
        )

    def list_subnets(self, **kwargs):
        """Lists the subnets in the specified VCN and the specified compartment."""
        compartment_id = self.get_argument("compartment_id", default=COMPARTMENT_OCID)
        vcn_id = self.get_argument("vcn_id")
        return self.finish(
            AquaUIApp().list_subnets(
                compartment_id=compartment_id, vcn_id=vcn_id, **kwargs
            )
        )

    def list_private_endpoints(self, **kwargs):
        """Lists the private endpoints in the specified compartment."""
        compartment_id = self.get_argument("compartment_id", default=COMPARTMENT_OCID)
        resource_type = self.get_argument(
            "resource_type", default=PRIVATE_ENDPOINT_TYPE
        )
        return self.finish(
            AquaUIApp().list_private_endpoints(
                compartment_id=compartment_id, resource_type=resource_type, **kwargs
            )
        )

    def get_shape_availability(self, **kwargs):
        """For a given compartmentId, resource limit name, and scope, returns the number of available resources associated
        with the given limit."""
        compartment_id = self.get_argument("compartment_id", default=COMPARTMENT_OCID)
        instance_shape = self.get_argument("instance_shape")
        limit_name = self.get_argument("limit_name")

        return self.finish(
            AquaUIApp().get_shape_availability(
                compartment_id=compartment_id,
                instance_shape=instance_shape,
                limit_name=limit_name,
                **kwargs,
            )
        )

    def is_bucket_versioned(self):
        """For a given compartmentId, resource limit name, and scope, returns the number of available resources associated
        with the given limit."""
        bucket_uri = self.get_argument("bucket_uri")
        return self.finish(AquaUIApp().is_bucket_versioned(bucket_uri=bucket_uri))


class AquaCLIHandler(AquaAPIhandler):
    """Handler for Aqua model import
    command_interface_map is a map of command+subcommand to corresponding API dataclas.
    Eg. In command `ads aqua model register ....`, command is `model` and subcommand is `register`
    The key in the map will be f"{command}_{sub_command}" and value will be a DataClass
    """

    command_interface_map = {"model_register": ImportModelDetails}

    @handle_exceptions
    def post(self, *args, **kwargs):
        """Handles cli command construction

        Raises
        ------
        HTTPError
            Raises HTTPError if inputs are missing or are invalid.
        """
        try:
            input_data = self.get_json_body()
        except Exception:
            raise HTTPError(400, Errors.INVALID_INPUT_DATA_FORMAT)

        if not input_data:
            raise HTTPError(400, Errors.NO_INPUT_DATA)

        validate_function_parameters(data_class=CLIDetails, input_data=input_data)
        command_details = CLIDetails(**input_data)

        interface = AquaCLIHandler.command_interface_map[
            f"{command_details.command}_{command_details.subcommand}"
        ]

        validate_function_parameters(
            data_class=interface, input_data=command_details.payload
        )
        payload = interface(**command_details.payload)
        self.finish({"command": payload.build_cli()})


__handlers__ = [
    ("logging/?([^/]*)", AquaUIHandler),
    ("compartments/?([^/]*)", AquaUIHandler),
    # TODO: change url to evaluation/experiments/?([^/]*)
    ("experiment/?([^/]*)", AquaUIHandler),
    ("modeldeployment/?([^/]*)", AquaUIHandler),
    ("versionsets/?([^/]*)", AquaUIHandler),
    ("buckets/?([^/]*)", AquaUIHandler),
    ("job/shapes/?([^/]*)", AquaUIHandler),
    ("vcn/?([^/]*)", AquaUIHandler),
    ("subnets/?([^/]*)", AquaUIHandler),
    ("privateendpoints/?([^/]*)", AquaUIHandler),
    ("shapes/limit/?([^/]*)", AquaUIHandler),
    ("bucket/versioning/?([^/]*)", AquaUIHandler),
    ("containers/?([^/]*)", AquaUIHandler),
    ("cli/?([^/]*)", AquaCLIHandler),
    ("capacityreservations/?([^/]*)", AquaUIHandler),
]
