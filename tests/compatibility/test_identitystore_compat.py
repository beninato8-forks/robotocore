"""Identity Store compatibility tests."""

import uuid

import pytest

from tests.compatibility.conftest import make_client

IDENTITY_STORE_ID = "d-1234567890"


@pytest.fixture
def identitystore():
    return make_client("identitystore")


def _unique(prefix="test"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


class TestIdentityStoreUsers:
    def test_list_users_empty(self, identitystore):
        response = identitystore.list_users(IdentityStoreId=IDENTITY_STORE_ID)
        assert "Users" in response
        assert isinstance(response["Users"], list)

    def test_create_user(self, identitystore):
        username = _unique("user")
        response = identitystore.create_user(
            IdentityStoreId=IDENTITY_STORE_ID,
            UserName=username,
            DisplayName="Test User",
            Name={"GivenName": "Test", "FamilyName": "User"},
        )
        assert response["IdentityStoreId"] == IDENTITY_STORE_ID
        assert "UserId" in response

    def test_describe_user(self, identitystore):
        username = _unique("user")
        create_resp = identitystore.create_user(
            IdentityStoreId=IDENTITY_STORE_ID,
            UserName=username,
            DisplayName="Describe Me",
            Name={"GivenName": "Desc", "FamilyName": "User"},
        )
        user_id = create_resp["UserId"]

        response = identitystore.describe_user(
            IdentityStoreId=IDENTITY_STORE_ID,
            UserId=user_id,
        )
        assert response["UserId"] == user_id
        assert response["UserName"] == username
        assert response["DisplayName"] == "Describe Me"

    def test_delete_user(self, identitystore):
        username = _unique("user")
        create_resp = identitystore.create_user(
            IdentityStoreId=IDENTITY_STORE_ID,
            UserName=username,
            DisplayName="Delete Me",
            Name={"GivenName": "Del", "FamilyName": "User"},
        )
        user_id = create_resp["UserId"]

        identitystore.delete_user(
            IdentityStoreId=IDENTITY_STORE_ID,
            UserId=user_id,
        )

        # Verify user no longer appears in list
        users = identitystore.list_users(IdentityStoreId=IDENTITY_STORE_ID)["Users"]
        user_ids = [u["UserId"] for u in users]
        assert user_id not in user_ids

    def test_list_users_returns_created(self, identitystore):
        username = _unique("user")
        create_resp = identitystore.create_user(
            IdentityStoreId=IDENTITY_STORE_ID,
            UserName=username,
            DisplayName="Listed User",
            Name={"GivenName": "List", "FamilyName": "User"},
        )
        user_id = create_resp["UserId"]

        users = identitystore.list_users(IdentityStoreId=IDENTITY_STORE_ID)["Users"]
        user_ids = [u["UserId"] for u in users]
        assert user_id in user_ids


class TestIdentityStoreGroups:
    def test_list_groups_empty(self, identitystore):
        response = identitystore.list_groups(IdentityStoreId=IDENTITY_STORE_ID)
        assert "Groups" in response
        assert isinstance(response["Groups"], list)

    def test_create_group(self, identitystore):
        display_name = _unique("group")
        response = identitystore.create_group(
            IdentityStoreId=IDENTITY_STORE_ID,
            DisplayName=display_name,
        )
        assert response["IdentityStoreId"] == IDENTITY_STORE_ID
        assert "GroupId" in response

    def test_describe_group(self, identitystore):
        display_name = _unique("group")
        create_resp = identitystore.create_group(
            IdentityStoreId=IDENTITY_STORE_ID,
            DisplayName=display_name,
        )
        group_id = create_resp["GroupId"]

        response = identitystore.describe_group(
            IdentityStoreId=IDENTITY_STORE_ID,
            GroupId=group_id,
        )
        assert response["GroupId"] == group_id
        assert response["DisplayName"] == display_name

    def test_delete_group(self, identitystore):
        display_name = _unique("group")
        create_resp = identitystore.create_group(
            IdentityStoreId=IDENTITY_STORE_ID,
            DisplayName=display_name,
        )
        group_id = create_resp["GroupId"]

        identitystore.delete_group(
            IdentityStoreId=IDENTITY_STORE_ID,
            GroupId=group_id,
        )

        groups = identitystore.list_groups(IdentityStoreId=IDENTITY_STORE_ID)["Groups"]
        group_ids = [g["GroupId"] for g in groups]
        assert group_id not in group_ids

    def test_list_groups_returns_created(self, identitystore):
        display_name = _unique("group")
        create_resp = identitystore.create_group(
            IdentityStoreId=IDENTITY_STORE_ID,
            DisplayName=display_name,
        )
        group_id = create_resp["GroupId"]

        groups = identitystore.list_groups(IdentityStoreId=IDENTITY_STORE_ID)["Groups"]
        group_ids = [g["GroupId"] for g in groups]
        assert group_id in group_ids


class TestIdentityStoreGroupMembership:
    def test_create_group_membership(self, identitystore):
        user = identitystore.create_user(
            IdentityStoreId=IDENTITY_STORE_ID,
            UserName=_unique("user"),
            DisplayName="Member",
            Name={"GivenName": "M", "FamilyName": "U"},
        )
        group = identitystore.create_group(
            IdentityStoreId=IDENTITY_STORE_ID,
            DisplayName=_unique("group"),
        )

        response = identitystore.create_group_membership(
            IdentityStoreId=IDENTITY_STORE_ID,
            GroupId=group["GroupId"],
            MemberId={"UserId": user["UserId"]},
        )
        assert "MembershipId" in response
        assert response["IdentityStoreId"] == IDENTITY_STORE_ID

    def test_list_group_memberships(self, identitystore):
        user = identitystore.create_user(
            IdentityStoreId=IDENTITY_STORE_ID,
            UserName=_unique("user"),
            DisplayName="Member",
            Name={"GivenName": "M", "FamilyName": "U"},
        )
        group = identitystore.create_group(
            IdentityStoreId=IDENTITY_STORE_ID,
            DisplayName=_unique("group"),
        )
        mem = identitystore.create_group_membership(
            IdentityStoreId=IDENTITY_STORE_ID,
            GroupId=group["GroupId"],
            MemberId={"UserId": user["UserId"]},
        )

        response = identitystore.list_group_memberships(
            IdentityStoreId=IDENTITY_STORE_ID,
            GroupId=group["GroupId"],
        )
        assert "GroupMemberships" in response
        membership_ids = [m["MembershipId"] for m in response["GroupMemberships"]]
        assert mem["MembershipId"] in membership_ids

    def test_delete_group_membership(self, identitystore):
        user = identitystore.create_user(
            IdentityStoreId=IDENTITY_STORE_ID,
            UserName=_unique("user"),
            DisplayName="Member",
            Name={"GivenName": "M", "FamilyName": "U"},
        )
        group = identitystore.create_group(
            IdentityStoreId=IDENTITY_STORE_ID,
            DisplayName=_unique("group"),
        )
        mem = identitystore.create_group_membership(
            IdentityStoreId=IDENTITY_STORE_ID,
            GroupId=group["GroupId"],
            MemberId={"UserId": user["UserId"]},
        )

        identitystore.delete_group_membership(
            IdentityStoreId=IDENTITY_STORE_ID,
            MembershipId=mem["MembershipId"],
        )

        response = identitystore.list_group_memberships(
            IdentityStoreId=IDENTITY_STORE_ID,
            GroupId=group["GroupId"],
        )
        membership_ids = [m["MembershipId"] for m in response["GroupMemberships"]]
        assert mem["MembershipId"] not in membership_ids


class TestIdentityStoreUpdateAndLookup:
    """Tests for Update, GetId, and membership lookup operations."""

    def test_get_group_id(self, identitystore):
        """GetGroupId returns the group ID for a unique attribute filter."""
        display_name = _unique("group")
        create_resp = identitystore.create_group(
            IdentityStoreId=IDENTITY_STORE_ID,
            DisplayName=display_name,
        )
        group_id = create_resp["GroupId"]

        resp = identitystore.get_group_id(
            IdentityStoreId=IDENTITY_STORE_ID,
            AlternateIdentifier={
                "UniqueAttribute": {
                    "AttributePath": "displayName",
                    "AttributeValue": display_name,
                }
            },
        )
        assert resp["GroupId"] == group_id
        assert resp["IdentityStoreId"] == IDENTITY_STORE_ID

    def test_get_user_id(self, identitystore):
        """GetUserId returns the user ID for a unique attribute filter."""
        username = _unique("user")
        create_resp = identitystore.create_user(
            IdentityStoreId=IDENTITY_STORE_ID,
            UserName=username,
            DisplayName="Get User ID",
            Name={"GivenName": "Get", "FamilyName": "User"},
        )
        user_id = create_resp["UserId"]

        resp = identitystore.get_user_id(
            IdentityStoreId=IDENTITY_STORE_ID,
            AlternateIdentifier={
                "UniqueAttribute": {
                    "AttributePath": "userName",
                    "AttributeValue": username,
                }
            },
        )
        assert resp["UserId"] == user_id
        assert resp["IdentityStoreId"] == IDENTITY_STORE_ID

    def test_list_group_memberships_for_member(self, identitystore):
        """ListGroupMembershipsForMember returns all groups a user belongs to."""
        user = identitystore.create_user(
            IdentityStoreId=IDENTITY_STORE_ID,
            UserName=_unique("user"),
            DisplayName="Multi Member",
            Name={"GivenName": "M", "FamilyName": "U"},
        )
        group1 = identitystore.create_group(
            IdentityStoreId=IDENTITY_STORE_ID,
            DisplayName=_unique("group"),
        )
        group2 = identitystore.create_group(
            IdentityStoreId=IDENTITY_STORE_ID,
            DisplayName=_unique("group"),
        )
        identitystore.create_group_membership(
            IdentityStoreId=IDENTITY_STORE_ID,
            GroupId=group1["GroupId"],
            MemberId={"UserId": user["UserId"]},
        )
        identitystore.create_group_membership(
            IdentityStoreId=IDENTITY_STORE_ID,
            GroupId=group2["GroupId"],
            MemberId={"UserId": user["UserId"]},
        )

        resp = identitystore.list_group_memberships_for_member(
            IdentityStoreId=IDENTITY_STORE_ID,
            MemberId={"UserId": user["UserId"]},
        )
        assert "GroupMemberships" in resp
        group_ids = [m["GroupId"] for m in resp["GroupMemberships"]]
        assert group1["GroupId"] in group_ids
        assert group2["GroupId"] in group_ids


class TestIdentityStoreErrors:
    """Tests for error handling on nonexistent resources."""

    def test_describe_user_nonexistent(self, identitystore):
        """DescribeUser for nonexistent user raises ResourceNotFoundException."""
        from botocore.exceptions import ClientError

        with pytest.raises(ClientError) as exc:
            identitystore.describe_user(
                IdentityStoreId=IDENTITY_STORE_ID,
                UserId="00000000-0000-0000-0000-000000000000",
            )
        assert exc.value.response["Error"]["Code"] == "ResourceNotFoundException"

    def test_describe_group_nonexistent(self, identitystore):
        """DescribeGroup for nonexistent group raises ResourceNotFoundException."""
        from botocore.exceptions import ClientError

        with pytest.raises(ClientError) as exc:
            identitystore.describe_group(
                IdentityStoreId=IDENTITY_STORE_ID,
                GroupId="00000000-0000-0000-0000-000000000000",
            )
        assert exc.value.response["Error"]["Code"] == "ResourceNotFoundException"


class TestIdentitystoreGroupMembership:
    """Tests for DescribeGroupMembership operation."""

    def test_describe_group_membership_nonexistent(self, identitystore):
        """DescribeGroupMembership with nonexistent membership ID raises ResourceNotFoundException."""  # noqa: E501
        from botocore.exceptions import ClientError

        with pytest.raises(ClientError) as exc:
            identitystore.describe_group_membership(
                IdentityStoreId=IDENTITY_STORE_ID,
                MembershipId="00000000-0000-0000-0000-000000000000",
            )
        assert exc.value.response["Error"]["Code"] == "ResourceNotFoundException"


class TestIdentitystoreUpdateOps:
    """Tests for UpdateUser and UpdateGroup operations."""

    def test_update_user(self, identitystore):
        """UpdateUser successfully updates a user attribute."""
        user_resp = identitystore.create_user(
            IdentityStoreId=IDENTITY_STORE_ID,
            UserName="update-test-user",
            DisplayName="Original Name",
            Name={"FamilyName": "Name", "GivenName": "Original"},
        )
        user_id = user_resp["UserId"]
        try:
            resp = identitystore.update_user(
                IdentityStoreId=IDENTITY_STORE_ID,
                UserId=user_id,
                Operations=[{"AttributePath": "displayName", "AttributeValue": "Updated Name"}],
            )
            assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200
        finally:
            identitystore.delete_user(IdentityStoreId=IDENTITY_STORE_ID, UserId=user_id)

    def test_update_group(self, identitystore):
        """UpdateGroup successfully updates a group attribute."""
        group_resp = identitystore.create_group(
            IdentityStoreId=IDENTITY_STORE_ID,
            DisplayName="Original Group",
        )
        group_id = group_resp["GroupId"]
        try:
            resp = identitystore.update_group(
                IdentityStoreId=IDENTITY_STORE_ID,
                GroupId=group_id,
                Operations=[{"AttributePath": "displayName", "AttributeValue": "Updated Group"}],
            )
            assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200
        finally:
            identitystore.delete_group(IdentityStoreId=IDENTITY_STORE_ID, GroupId=group_id)


class TestIdentitystoreMembershipLookup:
    """Tests for GetGroupMembershipId and IsMemberInGroups operations."""

    def test_get_group_membership_id(self, identitystore):
        """GetGroupMembershipId returns membership ID for a member in a group."""
        user_resp = identitystore.create_user(
            IdentityStoreId=IDENTITY_STORE_ID,
            UserName="membership-lookup-user",
            DisplayName="Lookup User",
            Name={"FamilyName": "User", "GivenName": "Lookup"},
        )
        uid = user_resp["UserId"]
        group_resp = identitystore.create_group(
            IdentityStoreId=IDENTITY_STORE_ID, DisplayName="Membership Lookup Group"
        )
        gid = group_resp["GroupId"]
        m_resp = identitystore.create_group_membership(
            IdentityStoreId=IDENTITY_STORE_ID,
            GroupId=gid,
            MemberId={"UserId": uid},
        )
        expected_mid = m_resp["MembershipId"]
        try:
            resp = identitystore.get_group_membership_id(
                IdentityStoreId=IDENTITY_STORE_ID,
                GroupId=gid,
                MemberId={"UserId": uid},
            )
            assert resp["MembershipId"] == expected_mid
        finally:
            identitystore.delete_group_membership(
                IdentityStoreId=IDENTITY_STORE_ID, MembershipId=expected_mid
            )
            identitystore.delete_user(IdentityStoreId=IDENTITY_STORE_ID, UserId=uid)
            identitystore.delete_group(IdentityStoreId=IDENTITY_STORE_ID, GroupId=gid)

    def test_is_member_in_groups(self, identitystore):
        """IsMemberInGroups returns membership status for each group."""
        user_resp = identitystore.create_user(
            IdentityStoreId=IDENTITY_STORE_ID,
            UserName="is-member-user",
            DisplayName="Is Member User",
            Name={"FamilyName": "User", "GivenName": "Member"},
        )
        uid = user_resp["UserId"]
        group_resp = identitystore.create_group(
            IdentityStoreId=IDENTITY_STORE_ID, DisplayName="IsMember Group"
        )
        gid = group_resp["GroupId"]
        m_resp = identitystore.create_group_membership(
            IdentityStoreId=IDENTITY_STORE_ID,
            GroupId=gid,
            MemberId={"UserId": uid},
        )
        mid = m_resp["MembershipId"]
        try:
            resp = identitystore.is_member_in_groups(
                IdentityStoreId=IDENTITY_STORE_ID,
                MemberId={"UserId": uid},
                GroupIds=[gid],
            )
            assert "Results" in resp
            assert len(resp["Results"]) == 1
            assert resp["Results"][0]["GroupId"] == gid
            assert resp["Results"][0]["MembershipExists"] is True
        finally:
            identitystore.delete_group_membership(
                IdentityStoreId=IDENTITY_STORE_ID, MembershipId=mid
            )
            identitystore.delete_user(IdentityStoreId=IDENTITY_STORE_ID, UserId=uid)
            identitystore.delete_group(IdentityStoreId=IDENTITY_STORE_ID, GroupId=gid)
