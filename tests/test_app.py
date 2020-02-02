import pandas as pd
import numpy as np
import pytest

import actions
import co2
import google



df_with_factors = pd.DataFrame(data=[['Bristol, UK', 'Bath, UK'], ['London, UK', 'London, UK']],
                  index=['from', 'to']).T


@pytest.fixture(scope='module')
def distance_matrix_unfactorized():
    yield google.get_distance_matrix_for_row(df_with_factors)


@pytest.fixture(scope='module')
def distance_df_factorized():
    """There's no equivalent to the raw mtx in the factorized version"""
    yield google.get_distances(df_with_factors)


def test_loading_data_with_header():

    with open('tests/test_data/data_with_header.xlsx', 'rb') as f:
        data = f.read()

    df = actions.parse_uploaded_file(data)

    assert len(df) == 2
    assert np.array_equal(df.columns, ['from', 'to'])


def test_loading_data_without_header():
    #TODO: test the handling of situations where people forget the header!
    pass


class TestSingleQueries:
    """These tests call GMaps and do not require the factorization of queries
    or the re-insertion into dataframes"""
    def test_processing_of_df_to_call_google_maps(self, distance_matrix_unfactorized):
        np.testing.assert_array_equal(distance_matrix_unfactorized['destination_addresses'], df_with_factors['to'])
        np.testing.assert_array_equal(distance_matrix_unfactorized['origin_addresses'], df_with_factors['from'])

    def test_directions_api_returns_results_equivalent_to_maps(self, distance_matrix_unfactorized):
        assert int(distance_matrix_unfactorized['rows'][0]['elements'][0]['distance']['value'] / 1000) == 189
        assert int(distance_matrix_unfactorized['rows'][1]['elements'][0]['distance']['value'] / 1000) == 184

    def test_unpacking_of_distance_mtx_to_list(self, distance_matrix_unfactorized):
        distance_list = google.unpack_distance_mtx_rows(distance_matrix_unfactorized)
        assert(len(distance_list)) == 4 # 2 x 2

        # Since there are two identical destinations, each origin should be duplicated
        assert distance_list[0] == distance_matrix_unfactorized['rows'][0]['elements'][1]
        assert distance_list[1] == distance_matrix_unfactorized['rows'][0]['elements'][1]

        assert distance_list[2] == distance_matrix_unfactorized['rows'][1]['elements'][1]
        assert distance_list[3] == distance_matrix_unfactorized['rows'][1]['elements'][1]


class TestCompositeQueries:
    def test_addition_of_distance_to_dataframe(self, distance_df_factorized):
        key = 'distances by car (km)'
        assert int(distance_df_factorized[key].iloc[0]) == 189
        assert int(distance_df_factorized[key].iloc[1]) == 184

    def test_addition_of_co2_to_dataframe(self, distance_df_factorized):
        key = 'emissions (kg CO2)'
        print(distance_df_factorized.columns)
        df = actions.add_carbon_estimates_to_df(distance_df_factorized)
        assert np.isclose(df[key].iloc[0], co2.calculate_co2(189), atol=.5)
        assert np.isclose(df[key].iloc[1], co2.calculate_co2(184), atol=.5)


# def test_grouping_of_queries_does_not_affect_df(distance_df_factorized):
#     grouped_df = google.group_queries(df_with_factors)
#     pd.testing.assert_frame_equal(grouped_df.explode('from').explode('to').reset_index(drop=True), df)
#
#
# def test_grouping_of_queries_does_not_affect_results():
#     dist