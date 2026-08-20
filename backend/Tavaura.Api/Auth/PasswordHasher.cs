using System.Security.Cryptography;
using Microsoft.AspNetCore.Identity;
using Tavaura.Api.Domain.Entities;

namespace Tavaura.Api.Auth;

public sealed class PasswordHasher
{
    private const string LegacyAlgorithm = "pbkdf2-sha256";
    private readonly Microsoft.AspNetCore.Identity.PasswordHasher<User> _identityHasher = new();
    private readonly User _dummyUser = new();
    private readonly string _dummyHash;

    public PasswordHasher()
    {
        _dummyHash = _identityHasher.HashPassword(_dummyUser, Convert.ToBase64String(RandomNumberGenerator.GetBytes(32)));
    }

    public string HashPassword(User user, string password)
    {
        return _identityHasher.HashPassword(user, password);
    }

    public PasswordVerificationResult VerifyPassword(User user, string password)
    {
        if (IsLegacyHash(user.PasswordHash))
        {
            return VerifyLegacyPassword(password, user.PasswordHash)
                ? PasswordVerificationResult.SuccessRehashNeeded
                : PasswordVerificationResult.Failed;
        }

        return _identityHasher.VerifyHashedPassword(user, user.PasswordHash, password);
    }

    public void VerifyDummyPassword(string password)
    {
        _ = _identityHasher.VerifyHashedPassword(_dummyUser, _dummyHash, password);
    }

    private static bool IsLegacyHash(string passwordHash)
    {
        return passwordHash.StartsWith($"{LegacyAlgorithm}.", StringComparison.Ordinal);
    }

    private static bool VerifyLegacyPassword(string password, string passwordHash)
    {
        var parts = passwordHash.Split('.');
        if (parts.Length != 4 || parts[0] != LegacyAlgorithm)
        {
            return false;
        }

        if (!int.TryParse(parts[1], out var iterations) || iterations <= 0)
        {
            return false;
        }

        try
        {
            var salt = Convert.FromBase64String(parts[2]);
            var expectedHash = Convert.FromBase64String(parts[3]);
            var actualHash = Rfc2898DeriveBytes.Pbkdf2(
                password,
                salt,
                iterations,
                HashAlgorithmName.SHA256,
                expectedHash.Length);

            return CryptographicOperations.FixedTimeEquals(actualHash, expectedHash);
        }
        catch (FormatException)
        {
            return false;
        }
    }
}
