import unittest
import numpy as np

from dedop.proc.sar.algorithms import StackMaskingAlgorithm
from dedop.proc.sar.surface_location_data import SurfaceLocationData, SurfaceType
from dedop.conf import CharacterisationFile, ConstantsFile

from tests.testing import TestDataLoader


class StackMaskingAlgorithmTests(unittest.TestCase):
    """
    test cases for the stack masking algorithm
    """

    chd_file = "test_data/common/chd.json"
    cst_file = "test_data/common/cst.json"

    inputs_01 = "test_data/proc/stack_masking_algorithm/" \
                "stack_masking_algorithm_01/input/inputs.txt"
    expected_01 = "test_data/proc/stack_masking_algorithm/" \
                  "stack_masking_algorithm_01/expected/expected.txt"

    inputs_02 = "test_data/proc/stack_masking_algorithm/" \
                "stack_masking_algorithm_02/input/inputs.txt"
    expected_02 = "test_data/proc/stack_masking_algorithm/" \
                  "stack_masking_algorithm_02/expected/expected.txt"

    def setUp(self):
        self.chd = CharacterisationFile(self.chd_file)
        self.cst = ConstantsFile(self.cst_file)
        self.stack_masking_algorithm = StackMaskingAlgorithm(self.chd, self.cst)

    def test_stack_masking_algorithm_01(self):
        """
        stack masking algorithm tests 01
        --------------------------------

        with raw surface
        """
        input_data = TestDataLoader(self.inputs_01, delim=' ')
        expected = TestDataLoader(self.expected_01, delim=' ')

        self._stack_masking_algorithm_tests(input_data, expected)

    def test_stack_masking_algorithm_02(self):
        """
        stack masking algorithm tests 02
        --------------------------------

        with RMC surface
        """
        input_data = TestDataLoader(self.inputs_02, delim=' ')
        expected = TestDataLoader(self.expected_02, delim=' ')

        self._stack_masking_algorithm_tests(input_data, expected)

    def _stack_masking_algorithm_tests(self, input_data, expected):
        """
        runs the stack masking algorithm test with provided input data
        and expected values

        :param input_data: TestDataLoader object containing inputs
        :param expected: TestDataLoader object containing expected values
        :return: None
        """

        stack_size = input_data["data_stack_size"]
        zp_fact_range = input_data["zp_fact_range_cnf"]

        beams_range_compr_samples =\
            np.tile(input_data["beams_range_compr"], 2)
        beams_range_compr = np.reshape(
            beams_range_compr_samples,
            (stack_size, self.chd.n_samples_sar * zp_fact_range)
        )

        working_loc = SurfaceLocationData(
            cst=self.cst, chd=self.chd,
            data_stack_size=stack_size,
            surface_type=SurfaceType(input_data["surface_type"]),
            doppler_corrections=input_data["doppler_corrections"],
            slant_range_corrections=input_data["slant_range_corrections"],
            win_delay_corrections=input_data["win_delay_corrections"],
            beams_range_compr=beams_range_compr
        )

        # set stack masking cnf parameters
        self.stack_masking_algorithm.rmc_margin =\
            StackMaskingAlgorithm.parameters["rmc_margin"].default_value
        self.stack_masking_algorithm.zp_fact_range =\
            zp_fact_range
        self.stack_masking_algorithm.n_looks_stack =\
            input_data["n_looks_stack_cnf"]
        self.stack_masking_algorithm.flag_avoid_zeros_in_multilooking = \
            StackMaskingAlgorithm.parameters["flag_avoid_zeros_in_multilooking"].default_value
        self.stack_masking_algorithm.flag_remove_doppler_ambiguities =\
            bool(input_data["flag_remove_doppler_ambiguities_cnf"])

        self.stack_masking_algorithm(working_loc)
        stack_mask_vector_actual = self.stack_masking_algorithm.stack_mask_vector
        beams_masked_actual = self.stack_masking_algorithm.beams_masked

        stack_mask_vector_expected = expected["stack_mask_vector"]
        beams_masked_expected = np.reshape(
            expected["beams_masked"],
            (stack_size, self.chd.n_samples_sar * zp_fact_range)
        )


        for stack_index in range(stack_size):
            # compare beams masked values
            for sample_index in range(self.chd.n_samples_sar * zp_fact_range):
                self.assertEqual(
                    beams_masked_actual[stack_index, sample_index],
                    beams_masked_expected[stack_index, sample_index],
                    msg="stack_index: {}/{}, sample_index: {}/{}".format(
                        stack_index, stack_size,
                        sample_index, self.chd.n_samples_sar
                    )
                )
            # compare stack mask vector value
            self.assertEqual(
                stack_mask_vector_actual[stack_index],
                stack_mask_vector_expected[stack_index],
                msg="stack_index: {}/{}".format(
                    stack_index, stack_size
                )
            )