/*
Copyright 2018 The Kubeflow Authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package gcp

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/pkg/errors"

	"github.com/kubeflow/fairing/kubeflow/pkg/fairing/constants"
)

type ServiceAccount struct {
	ProjectID string `json:"project_id"`
}

func ProjectID() (string, error) {
	secretPath := os.Getenv(constants.GoogleCredentialsEnv)
	if secretPath == "" {
		return "", fmt.Errorf("could not get credentials file path from env")
	}

	f, err := os.Open(secretPath)
	if err != nil {
		return "", errors.Wrap(err, "getting secret file")
	}
	defer f.Close()
	var sa *ServiceAccount
	d := json.NewDecoder(f)
	if err := d.Decode(&sa); err != nil {
		return "", errors.Wrap(err, "decoding credentials file")
	}

	return sa.ProjectID, nil
}
