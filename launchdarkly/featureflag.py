import launchdarkly_api
from launchdarkly_api.rest import ApiException
from launchdarkly_api.configuration import Configuration
from launchdarkly_api.models.patch_operation import PatchOperation
from launchdarkly_api.models.patch_comment import PatchComment
import copy
import time
import os
import dataclasses
from dictdiffer import diff

@dataclasses.dataclass
class ClauseOp:
    CONTAINS : str = "contains"
    IN : str = "in"

class LDRule():
    def __init__(self, description: str, **kwargs):
        self.description = description
        self.variation = kwargs.get('variation', None)
        self.rollout = kwargs.get('rollout', None)
        self.current_rules = kwargs.get('current_rules', None)
        self.rule = { k:v for k, v in launchdarkly_api.Rule(variation=self.variation, description=description).to_dict().items() if v is not None }


    def add_clause(self, attribute: str, op: ClauseOp, value):
        attribute = attribute
        op = op
        value = value
        new_clause = launchdarkly_api.Clause(op=op, attribute=attribute, values=[value])
        add_clause = { k:v for k, v in new_clause.to_dict().items() if v is not None }
        try:
            self.rule["clauses"] = [*self.rule["clauses"], add_clause]
        except KeyError:
            self.rule["clauses"] = [add_clause]
        return self

    def __iter__(self):
        for key in self.__dict__:
            yield key, getattr(self, key)

    def to_dict(self):
        self_dict = dict(self)["rule"]
        return { k:v for k, v in self_dict.items() if v is not None }

class LDFeatureFlagEnv(launchdarkly_api.FeatureFlagConfig):
    def __init__(self, config, project_key, flag_key, environment, comment="Python Booster"):
        self.api_instance = launchdarkly_api.FeatureFlagsApi(
            launchdarkly_api.ApiClient(config)
        )
        self.project_key = project_key
        self.flag_key = flag_key
        self.environment = environment
        self.patches = []
        self.comment = comment

    def __enter__(self) -> "LDFeatureFlag":
        if self.config.api_key == "":
            raise "API Key must be set"
        try:
            self.flag = self.api_instance.get_feature_flag(
                self.project_key, self.flag_key
            )
            self.current_flag = copy.deepcopy(self.flag)
        except ApiException as e:
            if e.status == 404:
                return "not found"
            else:
                print(e)
        return self

    def __exit__(self, *args) -> launchdarkly_api.FeatureFlag:
        self.generate_patch_name(self.patches)
        self.generate_patch_description(self.patches)
        self.generate_patch_csa(self.patches)
        print(self.patches)
        if len(self.patches) > 0:
            comment = dict(comment=self.comment, patch=self.patches)
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

class LDFeatureFlag(launchdarkly_api.FeatureFlag):
    def __init__(self, config, project_key, flag_key, environment):
        self.api_instance = launchdarkly_api.FeatureFlagsApi(
            launchdarkly_api.ApiClient(config)
        )
        self.project_key = project_key
        self.flag_key = flag_key
        self.patches = []
        self.environment = environment

    def __enter__(self) -> "LDFeatureFlag":
        print("entering")
        try:
            self.flag = self.api_instance.get_feature_flag(
                self.project_key, self.flag_key
            )
            self.current_flag = copy.deepcopy(self.flag)
            if self.environment:
                self.env = self.current_flag.environments[self.environment]
        except ApiException as e:
            if e.status == 404:
                return "not found"
            else:
                print(e)
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
            patch = {"op": "add", "value": tag, "path": f"/tags/${str(cur_idx)}"}
            self.patches.append(patch)

    def add_rules(self, rules):
        try: self.current_flag.environments[self.environment].rules
        except NameError: self.current_flag.environments[self.environment].rules = None

        if self.current_flag.environments[self.environment].rules:
            cur_rule_len = len(self.current_flag.environments[self.environment].rules)
        else:
            cur_rule_len = 0
        for idx, rule in enumerate(rules):
            cur_idx = cur_rule_len + idx
            print(rule.to_dict())
            #rule = { k:v for k, v in rule.to_dict().items() if v is not None }
            patch = {"op": "add", "value": rule.to_dict(), "path":f"/environments/{self.environment}/rules/{cur_idx}"}
            self.patches.append(patch)

config = Configuration()
if os.environ.get("LD_ACCESSTOKEN") != "":
    config.api_key["Authorization"] = os.environ.get("LD_ACCESSTOKEN")

#Testing Data
with LDFeatureFlag(config, project_key="demo-dan-101320-1", flag_key="chatbox", environment="development") as flag:
    flag.name = "new-test-name2"
    flag.description = "My New Description"
    # flag.client_side_availability.using_environment_id = True
    flag.add_tags(["test_tag", "new_tag"])
    #flag_clause = launchdarkly_api.Clause(op=ClauseOp.CONTAINS, attribute="test", values="yes")
    rules = [LDRule(variation=1, description="newRule", current_rules=flag.env.rules).add_clause("testAttr", ClauseOp.CONTAINS, "blah").add_clause("testAttr2", ClauseOp.CONTAINS, "testing")]
    rules.append(LDRule(variation=1, description="My Description").add_clause("testAttr3", ClauseOp.CONTAINS, "blah").add_clause("testAttr2", ClauseOp.CONTAINS, "another"))
    flag.add_rules(rules)
