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

package build

import (
	"fmt"
	"net/http"

	"github.com/google/go-containerregistry/pkg/v1/partial"

	"github.com/kubeflow/fairing/kubeflow/pkg/fairing/gcp"

	"github.com/google/go-containerregistry/pkg/authn"
	"github.com/google/go-containerregistry/pkg/name"
	"github.com/google/go-containerregistry/pkg/v1"
	"github.com/google/go-containerregistry/pkg/v1/mutate"
	"github.com/google/go-containerregistry/pkg/v1/remote"
	"github.com/google/go-containerregistry/pkg/v1/tarball"

	"github.com/pkg/errors"
)

// Build appends a tarball to a base image and uploads the new image
// base is the base image to append to
// tag is the new tag that will be uploaded
// tarPath is the path to a tarball that will be appended as a layer
func Build(base, tarPath, tag string) (string, error) {
	baseRef, err := name.ParseReference(base, name.WeakValidation)
	if err != nil {
		return "", errors.Wrap(err, "parsing source tag")
	}

	baseImage, err := remote.Image(baseRef, remote.WithAuthFromKeychain(authn.DefaultKeychain))
	if err != nil {
		return "", errors.Wrap(err, "getting source image ref")
	}

	l, err := tarball.LayerFromFile(tarPath)
	if err != nil {
		return "", errors.Wrapf(err, "generating layer from tarball %s", tarPath)
	}

	if tag == "" {
		dstTag, err := NewTag(l)
		if err != nil {
			return "", errors.Wrap(err, "")
		}
		tag = dstTag
	}

	image, err := mutate.AppendLayers(baseImage, l)
	if err != nil {
		return "", errors.Wrap(err, "appending layer")
	}

	if err := UploadImage(image, tag); err != nil {
		return "", errors.Wrapf(err, "uploading image %s", tag)
	}

	return tag, nil
}

func NewTag(l partial.WithDiffID) (string, error) {
	projectID, err := gcp.ProjectID()
	if err != nil {
		return "", errors.Wrap(err, "getting project id")
	}

	digest, err := l.DiffID()
	if err != nil {
		return "", errors.Wrap(err, "getting layer digest")
	}

	return fmt.Sprintf("gcr.io/%s/fairing-job:%s", projectID, digest.Hex[:6]), nil
}

// UploadImage uploads an image to a remote registry, using the default keychain
// for that registry.
func UploadImage(image v1.Image, tag string) error {
	dstTag, err := name.NewTag(tag, name.WeakValidation)
	if err != nil {
		return errors.Wrap(err, "parsing dst tag")
	}

	dstAuth, err := authn.DefaultKeychain.Resolve(dstTag.Context().Registry)
	if err != nil {
		return errors.Wrap(err, "getting credentials")
	}

	if err := remote.Write(dstTag, image, dstAuth, http.DefaultTransport); err != nil {
		return errors.Wrap(err, "uploading image")
	}
	return nil
}
