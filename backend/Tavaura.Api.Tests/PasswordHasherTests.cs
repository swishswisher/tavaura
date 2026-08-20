using System.Security.Cryptography;
using Microsoft.AspNetCore.Identity;
using Tavaura.Api.Auth;
using Tavaura.Api.Domain.Entities;
using Xunit;

namespace Tavaura.Api.Tests;

public class PasswordHasherTests
{
    [Fact]
    public void NewIdentityHashRoundTrips()
    {
        var hasher = new PasswordHasher();
        var user = new User();
        user.PasswordHash = hasher.HashPassword(user, "correct horse battery staple");

        Assert.NotEqual("correct horse battery staple", user.PasswordHash);
        Assert.NotEqual(
            PasswordVerificationResult.Failed,
            hasher.VerifyPassword(user, "correct horse battery staple"));
        Assert.Equal(
            PasswordVerificationResult.Failed,
            hasher.VerifyPassword(user, "incorrect password"));
    }

    [Fact]
    public void ValidLegacyHashRequiresUpgrade()
    {
        const string password = "legacy-password";
        const int iterations = 120_000;
        var salt = RandomNumberGenerator.GetBytes(16);
        var hash = Rfc2898DeriveBytes.Pbkdf2(
            password,
            salt,
            iterations,
            HashAlgorithmName.SHA256,
            32);
        var user = new User
        {
            PasswordHash = $"pbkdf2-sha256.{iterations}.{Convert.ToBase64String(salt)}.{Convert.ToBase64String(hash)}"
        };

        Assert.Equal(
            PasswordVerificationResult.SuccessRehashNeeded,
            new PasswordHasher().VerifyPassword(user, password));
    }
}
