import launchdarkly_api
from launchdarkly_api.rest import ApiException
from launchdarkly_api.configuration import Configuration
from launchdarkly_api.models.patch_operation import PatchOperation
from launchdarkly_api.models.patch_comment import PatchComment
import copy
import time


class LDFeatureFlag(launchdarkly_api.FeatureFlag):
    def __init__(self, config, project_key, flag_key):
        self.api_instance = launchdarkly_api.FeatureFlagsApi(
            launchdarkly_api.ApiClient(config)
        )
        self.project_key = project_key
        self.flag_key = flag_key
        self.patches = []

    def __enter__(self) -> "LDFeatureFlag":
        print("entering")
        try:
            self.flag = self.api_instance.get_feature_flag(
                self.project_key, self.flag_key
            )
            self.current_flag = copy.deepcopy(self.flag)
            print("stuff")
        except ApiException as e:
            if e.status == 404:
                return "not found"
            else:
                print("failed")
        return self

    def __exit__(self, *args) -> launchdarkly_api.FeatureFlag:
        self.generate_patch_name(self.patches)
        self.generate_patch_description(self.patches)
        self.generate_patch_csa(self.patches)
        print(self.patches)
        if len(self.patches) > 0:
            comment = dict(comment="selfGen", patch=self.patches)
            try:
                (
                    new_flag,
                    status,
                    headers,
                ) = self.api_instance.patch_feature_flag_with_http_info(
                    self.project_key, self.flag_key, comment
                )
            except ApiException as e:
                if e.status == 404:
                    return "not found"
                if e.status == 429:
                    current = time.time() * 1000.0
                    reset_rate = int(
                        (float(e.headers["X-RateLimit-Reset"]) - current + 1000.0) / 1000.0
                    )
                    time.sleep(reset_rate)
                print(e)

    def generate_patch_name(self, patches):
        if self.flag.name != self.current_flag.name:
            patch = {"op": "replace", "value": self.flag.name, "path": "/name"}
            patches.append(patch)
            return patches
        return None

    def generate_patch_description(self, patches):
        if self.flag.description != self.current_flag.description:
            patch = {
                "op": "replace",
                "value": self.flag.description,
                "path": "/description",
            }
            patches.append(patch)

    def generate_patch_description(self, patches):
        if self.flag.description != self.current_flag.description:
            patch = {
                "op": "replace",
                "value": self.flag.description,
                "path": "/description",
            }
            patches.append(patch)

    def generate_patch_csa(self, patches):
        if (
            self.flag.client_side_availability.using_environment_id
            != self.current_flag.client_side_availability.using_environment_id
        ):
            patch = {
                "op": "replace",
                "value": self.flag.client_side_availability.using_environment_id,
                "path": "/clientSideAvailability/usingEnvironmentId",
            }
            patches.append(patch)
        if (
            self.flag.client_side_availability.using_mobile_key
            != self.current_flag.client_side_availability.using_mobile_key
        ):
            patch = {
                "op": "replace",
                "value": self.flag.client_side_availability.using_mobile_key,
                "path": "/clientSideAvailability/usingMobileKey",
            }
            patches.append(patch)

    def generate_patch_tag(self, patches):
        if self.flag.tags != self.current_flag.tags:
            patch = {"op": "replace", "value": self.flag.tags, "path": "/tags"}
            patches.append(patch)

    def add_tags(self, tags):
        add_tags = set(tags).difference(self.current_flag.tags)
        for idx, tag in enumerate(add_tags):
            cur_idx = len(self.current_flag.tags) + idx
            patch = {"op": "add", "value": tag, "path": "/tags/" + str(cur_idx)}
            self.patches.append(patch)


config = Configuration()
config.api_key["Authorization"] = "api-1ae50b03-d7b1-4cbc-be80-ce987180d65e"
with LDFeatureFlag(config, "demo-dan-101320-1", "chatbox") as flag:
    flag.name = "new-test-name2"
    flag.description = "My New Description"
    # flag.client_side_availability.using_environment_id = True
    flag.add_tags(["test_tag", "new_tag"])
