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

package cmd

import (
	"fmt"
	"io"
	"time"

	"github.com/kubeflow/fairing/kubeflow/pkg/fairing/build"

	"github.com/pkg/errors"
	"github.com/spf13/cobra"
)

var (
	baseImage, dstImage, layerFile string
)

func NewCmdBuild(out io.Writer) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "build",
		Short: "builds an image from a tarball",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return RunBuild(out, cmd)
		},
	}

	cmd.Flags().StringVar(&baseImage, "base-image", "", "the base image to append to")
	cmd.Flags().StringVar(&layerFile, "layer-file", "", "a tar.gz file to append as a layer")
	cmd.Flags().StringVar(&dstImage, "dst-image", "", "the tag to push")

	cmd.Flags().VarP(versionFlag, "output", "o", versionFlag.Usage())
	return cmd
}

func RunBuild(out io.Writer, cmd *cobra.Command) error {
	start := time.Now()
	if baseImage == "" || layerFile == "" {
		return fmt.Errorf("base-image and layer-file are all required flags")
	}
	tag, err := build.Build(baseImage, layerFile, dstImage)
	if err != nil {
		return errors.Wrap(err, "running build")
	}
	fmt.Fprintln(out, "Completed build in", time.Since(start))
	fmt.Fprintf(out, "Image available at %s\n", tag)
	return nil
}
