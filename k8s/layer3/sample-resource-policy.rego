# Lab-only: Sample does not establish hardware/workload identity.
package policy

default allow = false

allow if {
    data.plugin == "resource"
    data.query == {}
    input["submods"]["cpu0"]["ear.veraison.annotated-evidence"]["sample"]
    data["resource-path"] in {
        ["default", "key", "minilm-l6-v2"],
        ["default", "test", "l3-synthetic"],
        ["default", "test", "wrong-aes"],
    }
}
